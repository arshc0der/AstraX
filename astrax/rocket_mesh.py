"""Procedural 3D rocket geometry (pure NumPy, no OpenGL). +Z is 'up', origin at base of first core stage.

build_rocket_parts(rocket, fuel_fractions=None) -> list[Part]; each Part has vertices (N,3), faces (M,3),
rgba colour and a name. The viewport turns Parts into GL meshes; tests/exports can use them directly.
load_obj() lets users import their own visual model (display only; physics uses the numeric design).
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np


@dataclass
class Part:
    name: str
    vertices: np.ndarray
    faces: np.ndarray
    color: tuple


def revolve(profile, segments=36, cap_start=True, cap_end=True):
    """Surface of revolution about +Z from a profile [(z, r), ...]."""
    prof = np.asarray(profile, float); n = len(prof)
    ang = np.linspace(0, 2 * math.pi, segments, endpoint=False)
    V = np.zeros((n * segments, 3))
    for i, (z, r) in enumerate(prof):
        V[i * segments:(i + 1) * segments] = np.c_[r * np.cos(ang), r * np.sin(ang), np.full(segments, z)]
    F = []
    for i in range(n - 1):
        for j in range(segments):
            a, b = i * segments + j, i * segments + (j + 1) % segments
            c, d = (i + 1) * segments + j, (i + 1) * segments + (j + 1) % segments
            F += [(a, c, b), (b, c, d)]
    extra = []
    for flag, idx, zc in ((cap_start, 0, prof[0][0]), (cap_end, n - 1, prof[-1][0])):
        if flag and prof[idx][1] > 1e-9:
            ci = len(V) + len(extra); extra.append([0, 0, zc])
            for j in range(segments):
                a, b = idx * segments + j, idx * segments + (j + 1) % segments
                F.append((ci, b, a) if idx == 0 else (ci, a, b))
    if extra: V = np.vstack([V, np.array(extra)])
    return V, np.array(F, dtype=np.int32)


def nose_profile(shape, length, radius, z0, n=24):
    """Nose-cone radius profile from base (t=0) to tip (t=1). Standard nose-cone shape equations."""
    t = np.linspace(0, 1, n)
    sx = 1 - t                           # distance from tip as a fraction of length
    if shape == "conic":
        r = radius * sx
    elif shape == "parabolic":           # K' = 1 parabola
        r = radius * (2 * sx - sx ** 2)
    elif shape == "elliptical":
        r = radius * np.sqrt(np.maximum(0, 1 - t ** 2))
    elif shape == "von_karman":          # Haack series, C = 0
        th = np.arccos(1 - 2 * sx)
        r = radius * np.sqrt(np.maximum(0, (th - np.sin(2 * th) / 2) / math.pi))
    else:                                # tangent ogive
        rho = (radius ** 2 + length ** 2) / (2 * radius)
        x = t * length                   # distance from the base
        r = np.maximum(0, np.sqrt(np.maximum(0, rho ** 2 - x ** 2)) + radius - rho)
    r = np.maximum(r, 0.0); r[-1] = 0.0
    return [(z0 + t[i] * length, float(r[i])) for i in range(n)]


def _box(center, size, color=None):
    cx, cy, cz = center; sx, sy, sz = (s / 2 for s in size)
    V = np.array([[cx + dx * sx, cy + dy * sy, cz + dz * sz] for dx in (-1, 1) for dy in (-1, 1) for dz in (-1, 1)])
    F = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    return V, F


def _fin(zb, r, chord_root, chord_tip, span, ang, thick=0.06):
    """Trapezoid fin radially outward at azimuth ang."""
    pts = np.array([[r, -thick / 2, zb], [r, thick / 2, zb], [r, -thick / 2, zb + chord_root], [r, thick / 2, zb + chord_root],
                    [r + span, -thick / 2, zb], [r + span, thick / 2, zb],
                    [r + span, -thick / 2, zb + chord_tip], [r + span, thick / 2, zb + chord_tip]])
    c, s = math.cos(ang), math.sin(ang)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    F = np.array([[0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3], [4, 6, 7], [4, 7, 5], [0, 1, 3], [0, 3, 2]])
    return pts @ R.T, F


def _leg(zb, r, length, ang, spread=0.55, thick=0.12):
    """Landing leg: a slim box from the hull (r, zb+0.45L) down/out to the foot."""
    top = np.array([r, 0, zb + length * 0.45]); foot = np.array([r + length * spread, 0, zb])
    d = foot - top; L = np.linalg.norm(d)
    V, F = _box((0, 0, 0), (thick, thick, L))
    V = V @ _align_z(d / L).T + (top + foot) / 2
    ca, sa = math.cos(ang), math.sin(ang)
    R = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
    return V @ R.T, F


def _align_z(d):
    z = np.array([0, 0, 1.0]); v = np.cross(z, d); c = float(np.dot(z, d))
    if np.linalg.norm(v) < 1e-9: return np.eye(3) if c > 0 else np.diag([1, -1, -1])
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def engine_offsets(count, placement, body_radius, nozzle_d):
    if count <= 1 or placement == "single": return [(0.0, 0.0)]
    if placement == "octaweb" and count >= 7:
        outer = count - 1; R = max(body_radius - nozzle_d * 0.55, nozzle_d)
        return [(0.0, 0.0)] + [(R * math.cos(2 * math.pi * k / outer), R * math.sin(2 * math.pi * k / outer)) for k in range(outer)]
    if placement == "cluster":
        n = math.ceil(math.sqrt(count)); pitch = nozzle_d * 1.05
        pts = [((i - (n - 1) / 2) * pitch, (j - (n - 1) / 2) * pitch) for i in range(n) for j in range(n)]
        return pts[:count]
    R = max(body_radius - nozzle_d * 0.55, nozzle_d * 0.6)   # ring
    return [(R * math.cos(2 * math.pi * k / count), R * math.sin(2 * math.pi * k / count)) for k in range(count)]


def _engine_part(eng, x, y, z_top, color=(0.25, 0.25, 0.28, 1)):
    d, L = eng.nozzle_diameter_m, eng.nozzle_length_m
    prof = [(z_top, d * 0.18), (z_top - L * 0.25, d * 0.22), (z_top - L * 0.7, d * 0.38), (z_top - L, d * 0.5)]
    V, F = revolve(prof, 20, cap_start=True, cap_end=False)
    V = V + np.array([x, y, 0]); return V, F


def _stage_parts(s, z_base, z_top, parts, tag, x_off=0.0, boosters_nose=False):
    r = s.diameter_m / 2; L = z_top - z_base
    if s.tank_split and L > 6:      # two-tone tank bands for a recognisable look
        cuts = [0, 0.04, 0.55, 0.57, 1.0]
        cols = [(0.3, 0.3, 0.33, 1), s.color, (0.2, 0.2, 0.22, 1), s.color]
    else:
        cuts, cols = [0, 1.0], [s.color]
    for k in range(len(cuts) - 1):
        z0, z1 = z_base + L * cuts[k], z_base + L * cuts[k + 1]
        V, F = revolve([(z0, r), (z1, r)], 40, cap_start=(k == 0), cap_end=False)
        V = V + np.array([x_off, 0, 0]); parts.append(Part(f"{tag}:{s.name}:body{k}", V, F, cols[k]))
    # engine bells
    for i, (ex, ey) in enumerate(engine_offsets(s.engine.count, s.engine.placement, r, s.engine.nozzle_diameter_m)):
        V, F = _engine_part(s.engine, ex + x_off, ey, z_base); parts.append(Part(f"{tag}:{s.name}:engine{i}", V, F, (0.22, 0.22, 0.25, 1)))
    for k in range(s.fin_count):
        V, F = _fin(z_base, r + x_off * 0, s.fin_root_chord_m, s.fin_tip_chord_m, s.fin_span_m, 2 * math.pi * k / s.fin_count + math.pi / 4)
        parts.append(Part(f"{tag}:{s.name}:fin{k}", V + np.array([x_off, 0, 0]), F, (0.15, 0.15, 0.18, 1)))
    for k in range(s.leg_count):
        V, F = _leg(z_base, r, s.leg_length_m, 2 * math.pi * k / s.leg_count)
        parts.append(Part(f"{tag}:{s.name}:leg{k}", V + np.array([x_off, 0, 0]), F, (0.5, 0.5, 0.55, 1)))


def build_rocket_parts(rocket, fuel_fractions=None) -> list:
    parts: list[Part] = []
    lay = rocket.stack_layout()
    for i, (s, zb, zt) in enumerate(lay):
        _stage_parts(s, zb, zt, parts, "core")
        if i + 1 < len(lay):    # interstage frustum
            nxt = lay[i + 1][0]
            V, F = revolve([(zt, s.diameter_m / 2), (zt + s.interstage_length_m, nxt.diameter_m / 2)], 40, False, False)
            parts.append(Part(f"interstage{i}", V, F, (0.12, 0.12, 0.14, 1)))
    ztop = lay[-1][2] if lay else 0.0
    n = rocket.nose
    V, F = revolve(nose_profile(n.shape, n.length_m, n.base_diameter_m / 2, ztop), 40, True, False)
    parts.append(Part("nose", V, F, n.color))
    # boosters: strapped on beside the first core stage
    boosters = rocket.boosters
    if boosters:
        b0 = lay[0][0].diameter_m / 2 if lay else 1.0
        total = sum(b.booster_count for b in boosters); k = 0
        for b in boosters:
            for j in range(b.booster_count):
                ang = 2 * math.pi * k / max(1, total) + math.pi / 2; k += 1
                off = b0 + b.diameter_m / 2 + 0.05
                tmp = []
                _stage_parts(b, 0.0, b.length_m, tmp, "booster", 0.0)
                nv, nf = revolve(nose_profile("conic", b.diameter_m * 1.2, b.diameter_m / 2, b.length_m), 24, True, False)
                tmp.append(Part("booster:nose", nv, nf, b.color))
                c, s_ = math.cos(ang), math.sin(ang); R = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
                for p in tmp:
                    parts.append(Part(f"booster{k}:{p.name}", (p.vertices + np.array([off, 0, 0])) @ R.T, p.faces, p.color))
    if rocket.custom_mesh_path:
        try:
            V, F = load_obj(rocket.custom_mesh_path); parts.append(Part("custom_obj", V, F, (0.8, 0.8, 0.9, 1)))
        except Exception:
            pass
    return parts


def load_obj(path):
    """Minimal Wavefront OBJ loader (v / f, triangulates polygons). Raises ValueError on empty files."""
    V, F = [], []
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            t = line.split()
            if not t: continue
            if t[0] == "v" and len(t) >= 4: V.append([float(x) for x in t[1:4]])
            elif t[0] == "f" and len(t) >= 4:
                idx = [int(x.split("/")[0]) for x in t[1:]]
                idx = [i - 1 if i > 0 else len(V) + i for i in idx]
                for k in range(1, len(idx) - 1): F.append([idx[0], idx[k], idx[k + 1]])
    if not V or not F: raise ValueError("OBJ has no geometry")
    return np.array(V, float), np.array(F, np.int32)


def export_obj(parts, path):
    """Write all parts to one OBJ file (users can open the rocket in Blender etc.)."""
    off = 1
    with open(path, "w") as f:
        f.write("# AstraX rocket export\n")
        for p in parts:
            f.write(f"o {p.name}\n")
            for v in p.vertices: f.write(f"v {v[0]:.5f} {v[1]:.5f} {v[2]:.5f}\n")
            for a, b, c in p.faces: f.write(f"f {a + off} {b + off} {c + off}\n")
            off += len(p.vertices)
