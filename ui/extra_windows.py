"""Extra user-created windows: additional 3D views (own camera) and live graph windows. All are floating, dockable docks."""
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel
from ui.viewport import SpaceViewport
from ui.telemetry import VARS, PALETTE


class ViewWindow(QDockWidget):
    CAMS = ["orbit", "follow_rocket", "launch", "first_person", "free"]

    def __init__(self, title, system, rocket, parent=None):
        super().__init__(title, parent); self.setObjectName(title); self.setFloating(True); self.resize(620, 460)
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(2, 2, 2, 2); row = QHBoxLayout()
        self.vp = SpaceViewport(); self.cam = QComboBox(); self.cam.addItems(["Orbit", "Follow rocket", "Launch camera", "First person", "Free"])
        self.cam.currentIndexChanged.connect(lambda i: self.vp.set_mode(self.CAMS[i])); row.addWidget(QLabel("Camera")); row.addWidget(self.cam)
        self.focus = QComboBox(); self.focus.addItems(["Rocket"] + [b.name for b in system.bodies]); self.focus.currentTextChanged.connect(self.vp.focus_on); row.addWidget(QLabel("Focus")); row.addWidget(self.focus); row.addStretch(1)
        v.addLayout(row); v.addWidget(self.vp, 1); self.setWidget(w)
        self.vp.init_bodies(system); self.vp.refresh_orbits(); self.vp.set_rocket(rocket); self.vp.set_mode("follow_rocket"); self.cam.setCurrentIndex(1)

    def rebuild(self, system, rocket):
        self.vp.init_bodies(system); self.vp.refresh_orbits(); self.vp.set_rocket(rocket)

    def on_snapshot(self, s): 
        if self.isVisible(): self.vp.update_scene(s)


class GraphWindow(QDockWidget):
    def __init__(self, title, get_rec, key="altitude_m", parent=None):
        super().__init__(title, parent); self.setObjectName(title); self.setFloating(True); self.resize(520, 340); self.get_rec = get_rec; self._tick = 0
        w = QWidget(); v = QVBoxLayout(w); self.combo = QComboBox()
        for k, lab, sc, u in VARS: self.combo.addItem(f"{lab} [{u}]" if u else lab, k)
        self.combo.setCurrentIndex([x[0] for x in VARS].index(key)); v.addWidget(self.combo)
        self.plot = pg.PlotWidget(); self.plot.setMinimumSize(120, 90); self.plot.setDownsampling(auto=True, mode="peak"); self.plot.showGrid(x=True, y=True, alpha=.25); v.addWidget(self.plot, 1); self.setWidget(w)

    def on_snapshot(self, s):
        self._tick += 1
        if self._tick % 12 or not self.isVisible(): return
        rec = self.get_rec(); key = self.combo.currentData()
        if rec is None or len(rec) < 2: return
        sc = next(x for x in VARS if x[0] == key); t, a = rec.arrays("met_s", key); a = a / sc[2]; a[~np.isfinite(a)] = np.nan
        self.plot.clear(); self.plot.setLabel("bottom", "Mission elapsed time", units="s"); self.plot.setLabel("left", sc[1], units=sc[3]); self.plot.plot(t, a, pen=pg.mkPen(PALETTE[0], width=2))
