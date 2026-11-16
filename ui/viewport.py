"""3D simulation viewport (PyOpenGL via pyqtgraph.opengl). Rendering only - no physics here.

Scene units are kilometres, positions are drawn relative to the focus object (avoids float32 jitter).
The rocket is drawn with a *visual* scale factor so it stays visible at planetary distances (shown in the overlay).
"""
import math
import numpy as np
import pyqtgraph.opengl as gl
from pyqtgraph import Transform3D
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from astrax.rocket_mesh import build_rocket_parts
from astrax.orbital import elements_to_state

LAYERS = ["Planet orbits", "Rocket trajectory", "Velocity vector", "Acceleration vector", "Gravity vectors",
          "Atmosphere boundary", "Axes", "Labels", "Info overlay", "Grid"]


def _merge(parts, scale=1.0):
    V, F, C, off = [], [], [], 0
    for p in parts:
        V.append(p.vertices * scale); F.append(p.faces + off); C.append(np.tile(np.array(p.color, float), (len(p.faces), 1))); off += len(p.vertices)
    return np.vstack(V).astype(np.float32), np.vstack(F).astype(np.int32), np.vstack(C).astype(np.float32)


class SpaceViewport(gl.GLViewWidget):
    def __init__(self):
        super().__init__()
        self.setBackgroundColor(QColor(2, 4, 8)); self.opts["fov"] = 50
        self.setCameraPosition(distance=2.5e8, elevation=30, azimuth=45)
        self.layers = {k: (k not in ("Atmosphere boundary", "Grid")) for k in LAYERS}
        self.mode = "orbit"; self.focus = "Earth"; self.body_scale = 1.0; self.trail_len = 3000
        self.body_items, self.label_items, self.orbit_items, self.atm_items = {}, {}, {}, {}
        self.rocket_item = None; self.rocket_height_km = 0.06; self.trail_abs = []; self.vec_items = {}
        self._rocket_key = None; self.system = None
        self.trail = gl.GLLinePlotItem(color=(1, .85, .1, 1), width=2, antialias=True); self.addItem(self.trail)
        self.axes = gl.GLAxisItem(); self.addItem(self.axes)
        self.grid = gl.GLGridItem(); self.grid.setSpacing(5, 5); self.grid.setSize(60, 60); self.addItem(self.grid)
        for name, col in (("v", (.2, 1, .4, 1)), ("a", (1, 1, .2, 1)), ("g", (1, .3, .3, 1))):
            it = gl.GLLinePlotItem(color=col, width=3, antialias=True); self.addItem(it); self.vec_items[name] = it
        self.overlay_text = ""

    # ---------------- setup ----------------
    def init_bodies(self, system):
        for d in (self.body_items, self.label_items, self.orbit_items, self.atm_items):
            for it in d.values(): self.removeItem(it)
            d.clear()
        self.system = system
        md = gl.MeshData.sphere(rows=24, cols=36)
        for b in system.bodies:
            m = gl.GLMeshItem(meshdata=md, smooth=True, color=b.color, shader="shaded", glOptions="opaque")
            self.addItem(m); self.body_items[b.name] = m
            t = gl.GLTextItem(text=b.name, color=(220, 230, 240, 255)); self.addItem(t); self.label_items[b.name] = t
            o = gl.GLLinePlotItem(color=(.35, .5, .7, .6), width=1, antialias=True); self.addItem(o); self.orbit_items[b.name] = o
            if b.atmosphere:
                a = gl.GLMeshItem(meshdata=md, smooth=True, color=(.4, .7, 1, .12), shader="balloon", glOptions="translucent")
                self.addItem(a); self.atm_items[b.name] = a

    def refresh_orbits(self):
        """Recompute static orbit ellipses from current (possibly edited) elements."""
        self._orbit_pts = {}
        for b in self.system.bodies:
            if b.a <= 0: continue
            pts = []
            for M in np.linspace(0, 360, 181):
                r, _ = elements_to_state(b.a, b.e, b.inc, b.raan, b.argp, M, 1e14)
                pts.append(r / 1000.0)
            self._orbit_pts[b.name] = np.array(pts)

    def set_rocket(self, rocket):
        parts = build_rocket_parts(rocket)
        V, F, C = _merge(parts, 1e-3)               # metres -> km
        V[:, 2] -= 0                                  # origin at base of stack
        if self.rocket_item is not None: self.removeItem(self.rocket_item)
        self.rocket_item = gl.GLMeshItem(vertexes=V, faces=F, faceColors=C, smooth=False, shader="shaded", glOptions="opaque")
        self.addItem(self.rocket_item); self.rocket_height_km = rocket.total_height_m / 1000.0
        self._com_km = rocket.center_of_mass() / 1000.0

    def set_layer(self, name, on): self.layers[name] = on

    # ---------------- camera ----------------
    def set_view(self, which):
        elev, az = {"top": (90, -90), "side": (0, 0), "front": (0, 90), "iso": (30, 45)}[which]
        self.setCameraPosition(elevation=elev, azimuth=az)

    def reset_camera(self):
        from pyqtgraph import Vector
        self.opts["center"] = Vector(0, 0, 0); self.setCameraPosition(distance=2.5e8 if self.focus != "Rocket" else 5.0, elevation=30, azimuth=45)

    def set_mode(self, mode):
        self.mode = mode
        if mode == "follow_rocket": self.focus = "Rocket"; self.setCameraPosition(distance=max(0.5, self.rocket_height_km * 12))
        elif mode == "first_person": self.focus = "Rocket"; self.setCameraPosition(distance=1e-3)
        self.reset_center()

    def reset_center(self):
        from pyqtgraph import Vector
        self.opts["center"] = Vector(0, 0, 0)

    def focus_on(self, name):
        self.focus = name; self.reset_center()
        b = self.system.get(name) if (self.system and name != "Rocket") else None
        self.setCameraPosition(distance=(b.radius_m / 1000.0 * 4) if b else max(0.5, self.rocket_height_km * 12))

    # ---------------- per-frame update ----------------
    def update_scene(self, snap):
        if self.system is None: return
        names = snap["names"]; bp = snap["bp"] / 1000.0; rp = snap["rp"] / 1000.0
        if self.focus == "Rocket": origin = rp
        else:
            origin = bp[names.index(self.focus)] if self.focus in names else np.zeros(3)
        cam = self.opts["distance"]
        for i, b in enumerate(self.system.bodies):
            c = bp[i] - origin; r = b.radius_m / 1000.0 * self.body_scale
            it = self.body_items[b.name]; it.resetTransform(); it.translate(*c); it.scale(r, r, r)
            lab = self.label_items[b.name]; lab.setVisible(self.layers["Labels"]); lab.setData(pos=c + np.array([0, 0, r * 1.2]))
            if b.name in self.atm_items:
                ra = (b.radius_m + b.atmosphere.top_altitude_m) / 1000.0 * self.body_scale
                a = self.atm_items[b.name]; a.setVisible(self.layers["Atmosphere boundary"]); a.resetTransform(); a.translate(*c); a.scale(ra, ra, ra)
            o = self.orbit_items[b.name]; ok = self.layers["Planet orbits"] and b.name in getattr(self, "_orbit_pts", {})
            o.setVisible(ok)
            if ok:
                par = bp[names.index(b.parent)] if b.parent else bp[0]
                o.setData(pos=(self._orbit_pts[b.name] + par - origin).astype(np.float32))
        # rocket
        d = snap["direction"] / max(np.linalg.norm(snap["direction"]), 1e-12); crel = rp - origin
        vis = max(1.0, cam * 0.03 / max(self.rocket_height_km, 1e-6))
        if self.mode == "first_person": vis = 1.0
        if self.rocket_item is not None:
            z = d; x = np.cross([0, 0, 1.0], z); x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-9 else np.array([1.0, 0, 0]); y = np.cross(z, x)
            s = vis; off = -z * self._com_km * s
            T = Transform3D(x[0] * s, y[0] * s, z[0] * s, crel[0] + off[0], x[1] * s, y[1] * s, z[1] * s, crel[1] + off[1],
                            x[2] * s, y[2] * s, z[2] * s, crel[2] + off[2], 0, 0, 0, 1)
            self.rocket_item.setTransform(T)
        # trajectory (absolute km stored, drawn relative)
        self.trail_abs.append(rp.copy())
        if len(self.trail_abs) > self.trail_len: self.trail_abs = self.trail_abs[-self.trail_len:]
        self.trail.setVisible(self.layers["Rocket trajectory"])
        if self.layers["Rocket trajectory"] and len(self.trail_abs) > 1:
            self.trail.setData(pos=(np.array(self.trail_abs) - origin).astype(np.float32))
        # vectors
        L = cam * 0.15
        def seg(vec):
            n = np.linalg.norm(vec); return None if n < 1e-12 else np.array([crel, crel + vec / n * L], np.float32)
        tm = snap["tm"]; v = snap["rv"] - (snap["bp"][names.index(tm["body"])] * 0)  # inertial velocity direction
        vv = seg(snap["rv"]); self.vec_items["v"].setVisible(self.layers["Velocity vector"] and vv is not None)
        if vv is not None: self.vec_items["v"].setData(pos=vv)
        aa = seg(snap["direction"] * max(tm["accel_thrust_ms2"], 0)); self.vec_items["a"].setVisible(self.layers["Acceleration vector"] and aa is not None)
        if aa is not None: self.vec_items["a"].setData(pos=aa)
        gi = names.index(tm["body"]); gvec = bp[gi] - rp
        gg = seg(gvec); self.vec_items["g"].setVisible(self.layers["Gravity vectors"] and gg is not None)
        if gg is not None: self.vec_items["g"].setData(pos=gg)
        self.axes.setVisible(self.layers["Axes"]); self.axes.setSize(cam * .2, cam * .2, cam * .2)
        self.grid.setVisible(self.layers["Grid"])
        if self.mode == "first_person":
            from pyqtgraph import Vector
            self.opts["center"] = Vector(*crel)
            az = math.degrees(math.atan2(d[1], d[0])); el = math.degrees(math.asin(max(-1, min(1, d[2]))))
            self.setCameraPosition(azimuth=az + 180, elevation=-el)
        self.overlay_text = (f"Focus: {self.focus}   Rocket drawn x{vis:,.0f} (visual scale)   Body size x{self.body_scale:g}" if self.layers["Info overlay"] else "")
        self.update()

    def clear_trail(self): self.trail_abs = []
