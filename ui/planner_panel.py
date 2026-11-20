"""Launch-window planner: Lambert porkchop plot (departure day x time of flight -> total delta-v) for interplanetary transfers."""
import datetime
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import pyqtSignal, QRectF
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QTextBrowser, QProgressBar, QGroupBox)
from astrax import transfer
from ui.worker_util import FuncWorker

PLANETS = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]
J2000 = datetime.datetime(2000, 1, 1, 12, 0)


def day_to_date(day): return (J2000 + datetime.timedelta(days=float(day))).strftime("%Y-%m-%d")


class PlannerPanel(QWidget):
    fly_requested = pyqtSignal(str, str, float, float)

    def __init__(self, system_getter):
        super().__init__(); self.S = system_getter; self.result = None; v = QVBoxLayout(self)
        g = QGroupBox("Transfer search (heliocentric, Lambert / patched conics, mean elements)"); f = QFormLayout(g)
        self.origin = QComboBox(); self.origin.addItems(PLANETS); self.origin.setCurrentText("Earth"); self.dest = QComboBox(); self.dest.addItems(PLANETS); self.dest.setCurrentText("Mars")
        f.addRow("From", self.origin); f.addRow("To", self.dest)
        self.start = QDoubleSpinBox(); self.start.setRange(-1e5, 1e5); self.start.setValue(0); self.start.setSuffix(" d after J2000"); f.addRow("Search start", self.start)
        self.span = QDoubleSpinBox(); self.span.setRange(30, 20000); self.span.setValue(800); self.span.setSuffix(" d"); f.addRow("Search span", self.span)
        self.tmin = QDoubleSpinBox(); self.tmin.setRange(20, 20000); self.tmin.setValue(120); self.tmin.setSuffix(" d"); self.tmax = QDoubleSpinBox(); self.tmax.setRange(30, 40000); self.tmax.setValue(350); self.tmax.setSuffix(" d")
        r = QHBoxLayout(); r.addWidget(self.tmin); r.addWidget(self.tmax); f.addRow("Time of flight min / max", r)
        self.n = QSpinBox(); self.n.setRange(10, 80); self.n.setValue(40); f.addRow("Grid resolution", self.n)
        self.park = QDoubleSpinBox(); self.park.setRange(100, 100000); self.park.setValue(300); self.park.setSuffix(" km"); f.addRow("Departure parking orbit altitude", self.park)
        v.addWidget(g)
        row = QHBoxLayout(); self.go = QPushButton("Compute launch windows"); self.go.setObjectName("primary"); self.go.clicked.connect(self.compute); row.addWidget(self.go)
        self.fly = QPushButton("Fly best transfer in 3D"); self.fly.setEnabled(False); self.fly.clicked.connect(self._fly); row.addWidget(self.fly); v.addLayout(row)
        self.bar = QProgressBar(); self.bar.setVisible(False); v.addWidget(self.bar)
        self.plot = pg.PlotWidget(); self.plot.setMinimumHeight(200); self.plot.setLabel("bottom", "Departure", units="days after J2000"); self.plot.setLabel("left", "Time of flight", units="days"); v.addWidget(self.plot, 1)
        self.img = pg.ImageItem(); self.plot.addItem(self.img); self.mark = pg.ScatterPlotItem(size=14, pen=pg.mkPen("w", width=2), brush=pg.mkBrush(None), symbol="o"); self.plot.addItem(self.mark)
        self.info = QTextBrowser(); self.info.setMaximumHeight(170); v.addWidget(self.info)

    def compute(self):
        s = self.S(); o, d = self.origin.currentText(), self.dest.currentText()
        if o == d: self.info.setHtml("Choose two different planets."); return
        self.go.setEnabled(False); self.bar.setVisible(True); self.bar.setRange(0, 100)
        self.w = FuncWorker(transfer.porkchop, s, o, d, self.start.value(), self.span.value(), self.tmin.value(), self.tmax.value(), self.n.value(), self.n.value(), self.park.value() * 1e3, 300e3)
        self.w.progress.connect(lambda i, n, t: self.bar.setValue(int(100 * i / max(n, 1)))); self.w.done.connect(self._done); self.w.failed.connect(lambda m: (self.info.setHtml(f"Failed: {m}"), self.go.setEnabled(True), self.bar.setVisible(False))); self.w.start()

    def _done(self, r):
        self.go.setEnabled(True); self.bar.setVisible(False); self.result = r; z = r["dv_total"]; ok = np.isfinite(z)
        if not ok.any() or r["best"] is None: self.info.setHtml("No valid transfers in this search window."); self.fly.setEnabled(False); return
        lo, hi = float(np.nanmin(z)), float(np.nanpercentile(z, 70)); cm = pg.colormap.get("viridis"); self.img.setLookupTable(cm.getLookupTable(0.0, 1.0, 256))
        self.img.setImage(np.nan_to_num(z, nan=hi), autoLevels=False, levels=(lo, max(hi, lo + 1)))
        dep, tof = r["dep_days"], r["tof_days"]; self.img.setRect(QRectF(dep[0], tof[0], dep[-1] - dep[0], tof[-1] - tof[0])); b = r["best"]; self.mark.setData([b["dep_day"]], [b["tof_days"]])
        s = self.S(); T = transfer.synodic_period_days(s, r["origin"], r["dest"]); t = transfer.transfer_for(s, r["origin"], r["dest"], b["dep_day"], b["tof_days"], self.park.value() * 1e3)
        self.info.setHtml(f"<b>Best window: {r['origin']} -> {r['dest']}</b><br>Depart <b>{day_to_date(b['dep_day'])}</b> (day {b['dep_day']:.0f}), arrive {day_to_date(b['dep_day'] + b['tof_days'])}, time of flight <b>{b['tof_days']:.0f} d</b><br>"
                          f"v-infinity departure {t['vinf_dep'] / 1e3:.2f} km/s (C3 = {t['c3'] / 1e6:.1f} km<sup>2</sup>/s<sup>2</sup>), arrival {t['vinf_arr'] / 1e3:.2f} km/s<br>"
                          f"Departure burn from {self.park.value():.0f} km orbit: {t['dv_dep']:,.0f} m/s; capture burn (300 km): {t['dv_arr']:,.0f} m/s; <b>total {t['dv_total']:,.0f} m/s</b><br>"
                          f"Synodic period {T:,.0f} d (windows repeat about every {T / 30.44:.0f} months).<br><i>Mean-element model: dates are indicative, not for mission design.</i>")
        self.fly.setEnabled(True)

    def _fly(self):
        if self.result and self.result["best"]:
            b = self.result["best"]; self.fly_requested.emit(self.result["origin"], self.result["dest"], b["dep_day"], b["tof_days"])
