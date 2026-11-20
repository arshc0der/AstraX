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
import random
from astrax.rocket_mesh import build_rocket_parts, _box
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
        self.grid = gl.GLGridItem(); self.grid.setSpacing(1e7, 1e7); self.grid.setSize(2e8, 2e8); self.addItem(self.grid)   # spacing FIRST: setSize triggers line generation
        for name, col in (("v", (.2, 1, .4, 1)), ("a", (1, 1, .2, 1)), ("g", (1, .3, .3, 1))):
            it = gl.GLLinePlotItem(color=col, width=3, antialias=True); self.addItem(it); self.vec_items[name] = it
        self.overlay_text = ""
        self.perf = False; self._every = 1; self._frame = 0; self._rc = (24, 36); self._buf = np.zeros((50000, 3)); self._tn = 0
        self.gl_info = None; self.on_gl_info = None
        cone = gl.MeshData.cylinder(rows=1, cols=20, radius=[1.0, 0.0], length=1.0)
        self.plume = gl.GLMeshItem(meshdata=cone, smooth=True, color=(1.0, 0.55, 0.15, 0.55), shader=None, glOptions="additive"); self.plume.setVisible(False); self.addItem(self.plume)
        self.plume_core = gl.GLMeshItem(meshdata=cone, smooth=True, color=(1.0, 0.95, 0.75, 0.8), shader=None, glOptions="additive"); self.plume_core.setVisible(False); self.addItem(self.plume_core)
        self.debris_item = gl.GLScatterPlotItem(pos=np.zeros((1, 3), np.float32), size=5, color=(1, .6, .2, 1), pxMode=True); self.debris_item.setVisible(False); self.addItem(self.debris_item)
        self.flash = gl.GLMeshItem(meshdata=gl.MeshData.sphere(rows=12, cols=18), smooth=True, color=(1, .7, .2, .5), shader=None, glOptions="additive"); self.flash.setVisible(False); self.addItem(self.flash)
        self.pred = gl.GLLinePlotItem(color=(.4, 1, .9, 1), width=2, antialias=True); self.pred.setVisible(False); self.addItem(self.pred)
        self.pred_pts = None; self.pred_body = None; self.capsule_item = None; self.pad_item = None; self.show_plume = True; self.rocket_radius_km = 0.002
        self.banner_events = []

    def set_space_background(self, hex_color: str):
        """Viewport clear colour (the theme background on dark themes)."""
        self.setBackgroundColor(QColor(hex_color))

    # ---------------- setup ----------------
    def init_bodies(self, system):
        for d in (self.body_items, self.label_items, self.orbit_items, self.atm_items):
            for it in d.values(): self.removeItem(it)
            d.clear()
        self.system = system
        md = gl.MeshData.sphere(rows=self._rc[0], cols=self._rc[1])
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
            if b.name in self.orbit_items: self.orbit_items[b.name].setData(pos=self._orbit_pts[b.name].astype(np.float32))

    def set_rocket(self, rocket):
        parts = build_rocket_parts(rocket)
        V, F, C = _merge(parts, 1e-3)               # metres -> km
        V[:, 2] -= 0                                  # origin at base of stack
        if self.rocket_item is not None: self.removeItem(self.rocket_item)
        self.rocket_item = gl.GLMeshItem(vertexes=V, faces=F, faceColors=C, smooth=False, shader="shaded", glOptions="opaque")
        self.addItem(self.rocket_item); self.rocket_height_km = rocket.total_height_m / 1000.0; self.rocket_radius_km = rocket.diameter_m / 2000.0
        for it in (self.capsule_item, self.pad_item):
            if it is not None: self.removeItem(it)
        nose = [p for p in parts if p.name == "nose"]
        if nose:
            cv, cf, cc = _merge(nose, 1e-3); self.capsule_item = gl.GLMeshItem(vertexes=cv, faces=cf, faceColors=cc, smooth=False, shader="shaded"); self.capsule_item.setVisible(False); self.addItem(self.capsule_item)
        pv, pf = _box((0, 0, -1.5), (40, 40, 3.0)); self.pad_item = gl.GLMeshItem(vertexes=(pv * 1e-3).astype(np.float32), faces=pf.astype(np.int32), color=(.45, .45, .5, 1), smooth=False, shader="shaded"); self.addItem(self.pad_item)
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
        elif mode == "launch": self.focus = "Rocket"; self.setCameraPosition(distance=max(0.2, self.rocket_height_km * 6))
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
        self._frame += 1; heavy = (self._frame % self._every == 0)
        if self.focus == "Rocket": origin = rp
        else:
            origin = bp[names.index(self.focus)] if self.focus in names else np.zeros(3)
        cam = self.opts["distance"]
        for i, b in enumerate(self.system.bodies):
            c = bp[i] - origin; r = b.radius_m / 1000.0 * self.body_scale
            it = self.body_items[b.name]; it.resetTransform(); it.translate(*c); it.scale(r, r, r)
            lab = self.label_items[b.name]; show_l = self.layers["Labels"] and not self.perf; lab.setVisible(show_l)
            if show_l and heavy: lab.setData(pos=c + np.array([0, 0, r * 1.2]))
            if b.name in self.atm_items:
                ra = (b.radius_m + b.atmosphere.top_altitude_m) / 1000.0 * self.body_scale
                a = self.atm_items[b.name]; a.setVisible(self.layers["Atmosphere boundary"] and not self.perf); a.resetTransform(); a.translate(*c); a.scale(ra, ra, ra)
            o = self.orbit_items[b.name]; ok = self.layers["Planet orbits"] and b.name in getattr(self, "_orbit_pts", {})
            o.setVisible(ok)
            if ok:      # geometry is uploaded once (refresh_orbits); per frame only a cheap GPU translation
                par = bp[names.index(b.parent)] if b.parent else bp[0]
                o.resetTransform(); o.translate(*(par - origin))
        # rocket
        d = snap["direction"] / max(np.linalg.norm(snap["direction"]), 1e-12); crel = rp - origin
        vis = max(1.0, cam * 0.03 / max(self.rocket_height_km, 1e-6))
        if self.mode == "first_person": vis = 1.0
        status = snap.get("status", "FLYING"); destroyed = status == "DESTROYED"; capsule = snap.get("capsule", False)
        if self.rocket_item is not None:
            z = d; x = np.cross([0, 0, 1.0], z); x = x / np.linalg.norm(x) if np.linalg.norm(x) > 1e-9 else np.array([1.0, 0, 0]); y = np.cross(z, x)
            s = vis; off = -z * self._com_km * s; base = crel + off
            T = Transform3D(x[0] * s, y[0] * s, z[0] * s, base[0], x[1] * s, y[1] * s, z[1] * s, base[1], x[2] * s, y[2] * s, z[2] * s, base[2], 0, 0, 0, 1)
            self.rocket_item.setVisible(not destroyed and not capsule); self.rocket_item.setTransform(T)
            if self.capsule_item is not None: self.capsule_item.setVisible(capsule and not destroyed); self.capsule_item.setTransform(T)
            if self.pad_item is not None: self.pad_item.setVisible(status == "PAD"); self.pad_item.setTransform(T)
            thr = snap.get("throttle", 0.0); burning = self.show_plume and thr > 0.01 and not destroyed and not capsule and status in ("FLYING", "PAD")
            for it, rk, lk in ((self.plume, 0.85, 1.0), (self.plume_core, 0.4, 0.55)):
                it.setVisible(burning)
                if burning:
                    R = self.rocket_radius_km * rk * s; Ln = self.rocket_height_km * 0.9 * thr * lk * (0.85 + 0.3 * random.random()) * s
                    it.setTransform(Transform3D(x[0] * R, y[0] * R, -z[0] * Ln, base[0], x[1] * R, y[1] * R, -z[1] * Ln, base[1], x[2] * R, y[2] * R, -z[2] * Ln, base[2], 0, 0, 0, 1))
        # debris (jettisoned stages = large white points, fragments = orange)
        dp = snap.get("debris_pos")
        if dp is not None and len(dp):
            kinds = snap["debris_kind"]
            col = np.array([(0.95, 0.95, 1.0, 1.0) if k == "stage" else (1.0, 0.55, 0.15, 1.0) for k in kinds], np.float32)
            sz = np.array([10.0 if k == "stage" else 4.0 for k in kinds], np.float32)
            self.debris_item.setData(pos=(dp / 1000.0 - origin).astype(np.float32), color=col, size=sz); self.debris_item.setVisible(True)
        else: self.debris_item.setVisible(False)
        ex = snap.get("explosion")
        if ex is not None and 0 <= snap["t"] - ex[0] < 4.0:
            age = snap["t"] - ex[0]; r_ = max(self.rocket_height_km * vis * 0.4, cam * 0.004) * (1 + 3 * age)
            self.flash.resetTransform(); self.flash.translate(*(ex[1] / 1000.0 - origin)); self.flash.scale(r_, r_, r_); self.flash.setColor((1, .7, .2, max(0.0, 0.6 * (1 - age / 4)))); self.flash.setVisible(True)
        else: self.flash.setVisible(False)
        if self.pred_pts is not None and self.pred_body in names:
            self.pred.setData(pos=(self.pred_pts + bp[names.index(self.pred_body)] - origin).astype(np.float32)); self.pred.setVisible(True)
        else: self.pred.setVisible(False)
        if self.mode == "launch":
            tm_ = snap["tm"]; up_ = np.array([tm_["rel_x"], tm_["rel_y"], tm_["rel_z"]]); up_ /= max(np.linalg.norm(up_), 1e-9)
            east = np.cross([0, 0, 1.0], up_); east = east / np.linalg.norm(east) if np.linalg.norm(east) > 1e-9 else np.array([0, 1.0, 0]); north = np.cross(up_, east)
            el, az = math.radians(8), math.radians(-35); dist = max(0.05, self.rocket_height_km * vis * 4)
            off_ = math.cos(el) * (math.cos(az) * north + math.sin(az) * east) + math.sin(el) * up_
            self.setCameraPosition(distance=dist, azimuth=math.degrees(math.atan2(off_[1], off_[0])), elevation=math.degrees(math.asin(max(-1, min(1, off_[2])))))
        # trajectory (absolute km stored, drawn relative)
        cap = min(self.trail_len, len(self._buf))           # ring buffer: O(1) append, no per-frame list->array conversion
        if self._tn < cap: self._buf[self._tn] = rp; self._tn += 1
        else: self._buf[:cap - 1] = self._buf[1:cap]; self._buf[cap - 1] = rp; self._tn = cap
        self.trail.setVisible(self.layers["Rocket trajectory"])
        if self.layers["Rocket trajectory"] and self._tn > 1 and heavy:
            self.trail.setData(pos=(self._buf[:self._tn] - origin).astype(np.float32))
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

    def clear_trail(self): self._tn = 0

    def set_quality(self, level: str):
        """'performance': lower sphere detail, no labels/atmosphere shells/line antialiasing, heavy items every 2nd frame."""
        perf = level == "performance"; rc = (12, 18) if perf else (24, 36); changed = rc != self._rc
        self.perf = perf; self._every = 2 if perf else 1; self._rc = rc
        for it in list(self.vec_items.values()) + [self.trail] + list(self.orbit_items.values()):
            it.antialias = not perf
        if changed and self.system is not None: self.init_bodies(self.system); self.refresh_orbits()

    def paintGL(self, *a, **k):
        if self.gl_info is None:                      # first frame: ask OpenGL which device is rendering
            try:
                from OpenGL.GL import glGetString, GL_RENDERER, GL_VENDOR, GL_VERSION
                dec = lambda v: v.decode() if isinstance(v, bytes) else str(v)
                self.gl_info = dict(renderer=dec(glGetString(GL_RENDERER)), vendor=dec(glGetString(GL_VENDOR)), version=dec(glGetString(GL_VERSION)))
            except Exception:
                self.gl_info = dict(renderer="unknown", vendor="", version="")
            if self.on_gl_info: self.on_gl_info(self.gl_info)
        return super().paintGL(*a, **k)

    def set_prediction(self, data):
        """data: (points_km_relative_to_body, body_name) or None to clear."""
        if data is None: self.pred_pts = None; self.pred_body = None
        else: self.pred_pts, self.pred_body = data
