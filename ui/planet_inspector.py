"""Planet / celestial body property inspector with editable simulation parameters and per-body reset."""
import math
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QListWidget, QDoubleSpinBox, QLabel, QPushButton, QGroupBox, QTextBrowser, QHBoxLayout, QFileDialog)
from astrax.bodies import REFERENCE_BODIES
from astrax.constants import G, AU
from astrax import project
import json


def _sp(lo, hi, dec, suf=""):
    s = QDoubleSpinBox(); s.setRange(lo, hi); s.setDecimals(dec); s.setSuffix(suf); s.setKeyboardTracking(False); s.setGroupSeparatorShown(True); return s


class PlanetInspector(QWidget):
    changed = pyqtSignal(str)            # body name edited / reset (simulation must be rebuilt)
    selected = pyqtSignal(str)

    def __init__(self, system):
        super().__init__(); self.system = system; self._loading = False
        v = QVBoxLayout(self); self.list = QListWidget(); self.list.setMaximumHeight(170); v.addWidget(self.list)
        for b in system.bodies: self.list.addItem(b.name)
        self.list.currentTextChanged.connect(self._show)
        g = QGroupBox("Editable simulation parameters"); f = QFormLayout(g)
        self.w = {}
        spec = [("mass", "Mass", 1e10, 1e33, 6, " kg", "Editing mass rescales GM = G*M"), ("radius_km", "Radius", 0.1, 1e7, 3, " km", ""),
                ("rot_h", "Rotation period (sidereal, <0 retrograde)", -1e6, 1e6, 4, " h", ""), ("tilt", "Axial tilt", 0, 180, 3, " deg", ""),
                ("a_au", "Semi-major axis", 0, 1e4, 6, " AU", "Heliocentric, or km-based for moons (see below)"), ("e", "Eccentricity", 0, 0.99, 6, "", ""),
                ("inc", "Inclination", -180, 180, 4, " deg", ""), ("raan", "Long. of ascending node", -360, 720, 4, " deg", ""), ("argp", "Argument of periapsis", -360, 720, 4, " deg", ""),
                ("m0", "Mean anomaly at epoch", -360, 720, 4, " deg", "")]
        for key, label, lo, hi, dec, suf, tip in spec:
            s = _sp(lo, hi, dec, suf); s.setToolTip(tip); s.editingFinished.connect(self._edited); self.w[key] = s; f.addRow(label, s)
        v.addWidget(g)
        g = QGroupBox("Derived (read-only)"); self.derived = QLabel(); self.derived.setObjectName("mono"); self.derived.setWordWrap(True); gv = QVBoxLayout(g); gv.addWidget(self.derived); v.addWidget(g)
        g = QGroupBox("Atmosphere"); self.atm = QLabel(); self.atm.setWordWrap(True); gv = QVBoxLayout(g); gv.addWidget(self.atm); v.addWidget(g)
        self.src = QTextBrowser(); self.src.setMaximumHeight(110); v.addWidget(QLabel("Data sources, epoch & limitations")); v.addWidget(self.src)
        self.state = QLabel(); v.addWidget(self.state)
        row = QHBoxLayout(); b = QPushButton("Reset to default"); b.setToolTip("Restore this body's reference values"); b.clicked.connect(self._reset); row.addWidget(b)
        b2 = QPushButton("Reset ALL"); b2.clicked.connect(self._reset_all); row.addWidget(b2); v.addLayout(row)
        row = QHBoxLayout(); b3 = QPushButton("Save planet config..."); b3.clicked.connect(self._save); b4 = QPushButton("Load..."); b4.clicked.connect(self._load); row.addWidget(b3); row.addWidget(b4); v.addLayout(row)
        v.addStretch(1); self.list.setCurrentRow(3)

    def set_system(self, system): self.system = system; self._show(self.list.currentItem().text() if self.list.currentItem() else "Earth")

    def _scale(self, b): return 1000.0 if b.parent else AU      # moon semi-major axis in km, planets in AU

    def _show(self, name):
        if not name: return
        b = self.system.get(name); self._loading = True; sc = self._scale(b)
        vals = dict(mass=b.mass, radius_km=b.radius_m / 1000, rot_h=b.rotation_period_s / 3600, tilt=b.axial_tilt_deg, a_au=b.a / sc, e=b.e, inc=b.inc, raan=b.raan, argp=b.argp, m0=b.m0)
        for k, v in vals.items(): self.w[k].setValue(v)
        self.w["a_au"].setSuffix(" km" if b.parent else " AU"); self.w["a_au"].setEnabled(b.a > 0)
        for k in ("e", "inc", "raan", "argp", "m0"): self.w[k].setEnabled(b.a > 0)
        T = self.system.orbital_period(name)
        self.derived.setText(f"GM            {b.gm:.9e} m^3/s^2\nMean density  {b.mean_density:,.1f} kg/m^3\nSurface gravity {b.surface_gravity:.3f} m/s^2\n"
                             f"Escape speed  {b.escape_velocity / 1000:.3f} km/s\nOrbital period {('%.3f d' % (T / 86400)) if T else '-'}\nSurface temp  {b.surface_temp_k or '-'} K")
        a = b.atmosphere
        self.atm.setText("None" if a is None else f"{a.composition}\nSurface pressure {a.surface_pressure_pa:,.0f} Pa, density {a.surface_density} kg/m^3\nScale height {a.scale_height_m / 1000:.1f} km, top {a.top_altitude_m / 1000:.0f} km")
        self.src.setHtml(f"<b>{b.source}</b><br>Epoch: J2000.0. Mean elements are approximate (not a full ephemeris); rotation poles simplified.")
        mod = self.system.is_modified(name); self.state.setText("<span style='color:#fbbf24'>MODIFIED from reference data</span>" if mod else "<span style='color:#34d399'>Reference values</span>")
        self._loading = False; self.selected.emit(name)

    def _edited(self):
        if self._loading or not self.list.currentItem(): return
        name = self.list.currentItem().text(); b = self.system.get(name); w = {k: s.value() for k, s in self.w.items()}; sc = self._scale(b)
        b.gm = G * w["mass"]; b.radius_m = w["radius_km"] * 1000; b.rotation_period_s = w["rot_h"] * 3600; b.axial_tilt_deg = w["tilt"]
        if b.a > 0: b.a = w["a_au"] * sc; b.e = w["e"]; b.inc = w["inc"]; b.raan = w["raan"]; b.argp = w["argp"]; b.m0 = w["m0"]
        self._show(name); self.changed.emit(name)

    def _reset(self):
        if self.list.currentItem(): n = self.list.currentItem().text(); self.system.reset_body(n); self._show(n); self.changed.emit(n)

    def _reset_all(self): self.system.reset_all(); self._show(self.list.currentItem().text()); self.changed.emit("*")

    def _save(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save planet configuration", "planets.json", "JSON (*.json)")
        if p: json.dump({"astrax_format": "planets/1", "planets": project.planets_to_dict(self.system)}, open(p, "w"), indent=2)

    def _load(self):
        p, _ = QFileDialog.getOpenFileName(self, "Load planet configuration", "", "JSON (*.json)")
        if p: project.apply_planets(self.system, json.load(open(p))["planets"]); self._show(self.list.currentItem().text()); self.changed.emit("*")
