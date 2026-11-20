"""Orbit analysis: how each event changed the orbit, maneuver planner (preview / predicted path / impulse), Hohmann helper."""
import math
import pyqtgraph as pg
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem, QDoubleSpinBox, QPushButton, QLabel, QFormLayout, QTextBrowser, QTabWidget)
from astrax.orbital import hohmann


def _fmt(x, unit="km", s=1e3):
    return "inf" if x == float("inf") else f"{x / s:,.1f} {unit}"


class OrbitPanel(QWidget):
    prediction_cleared = pyqtSignal()

    def __init__(self, worker_getter, recorder_getter):
        super().__init__(); self.W, self.R = worker_getter, recorder_getter; self._n = 0; self._tick = 0; self.snap = None
        v = QVBoxLayout(self); tabs = QTabWidget(); v.addWidget(tabs)
        # --- change log
        t = QWidget(); tv = QVBoxLayout(t)
        tv.addWidget(QLabel("How each event changed the orbit (osculating elements about the dominant body):", objectName="muted"))
        self.table = QTableWidget(0, 8); self.table.setHorizontalHeaderLabels(["MET s", "Event", "Body", "Perigee alt", "Apogee alt", "e", "Incl.", "Speed"]); self.table.horizontalHeader().setStretchLastSection(True); tv.addWidget(self.table)
        self.plot = pg.PlotWidget(); self.plot.setMinimumHeight(120); self.plot.showGrid(x=True, y=True, alpha=.25); self.plot.addLegend(); self.plot.setLabel("bottom", "Mission elapsed time", units="s"); self.plot.setLabel("left", "Altitude", units="km"); tv.addWidget(self.plot)
        tabs.addTab(t, "Orbit changes")
        # --- planner
        p = QWidget(); pv = QVBoxLayout(p); g = QGroupBox("Impulsive maneuver planner (ideal, instantaneous burn at current position)"); f = QFormLayout(g)
        self.dv = []
        for lab in ("Prograde (+) / retrograde (-)", "Normal (+) / anti-normal (-)", "Radial out (+) / in (-)"):
            s = QDoubleSpinBox(); s.setRange(-50000, 50000); s.setDecimals(1); s.setSuffix(" m/s"); self.dv.append(s); f.addRow(lab, s)
        pv.addWidget(g)
        row = QHBoxLayout()
        for txt, fn in (("Preview new orbit", self.preview), ("Draw predicted path", self.predict), ("Clear path", self.clear), ("Apply impulse now", self.apply)):
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
            if txt.startswith("Apply"): b.setObjectName("primary")
        pv.addLayout(row)
        self.out = QTextBrowser(); pv.addWidget(self.out)
        h = QGroupBox("Hohmann helper (circular orbit raise)"); hf = QFormLayout(h); self.target = QDoubleSpinBox(); self.target.setRange(100, 1e6); self.target.setValue(1000); self.target.setSuffix(" km altitude"); hf.addRow("Target altitude", self.target)
        b = QPushButton("Compute dv1 / dv2 and fill prograde"); b.clicked.connect(self.hohmann); hf.addRow(b); self.hlabel = QLabel(""); hf.addRow(self.hlabel); pv.addWidget(h)
        tabs.addTab(p, "Maneuver planner")

    def update_snapshot(self, snap):
        self.snap = snap; log = snap["orbit_log"]
        if len(log) != self._n:
            self._n = len(log); self.table.setRowCount(len(log))
            for i, e in enumerate(log):
                for j, val in enumerate([f"{e['met']:,.0f}", e["label"], e["body"], _fmt(e["peri_alt"]), _fmt(e["apo_alt"]), f"{e['e']:.4f}", f"{e['inc']:.2f}", f"{e['speed']:,.0f} m/s"]): self.table.setItem(i, j, QTableWidgetItem(val))
        self._tick += 1
        if self._tick % 20 == 0:
            rec = self.R()
            if rec is not None and len(rec) > 1:
                t, pe, ap = rec.arrays("met_s", "periapsis_alt_m", "apoapsis_alt_m"); ap = ap.copy(); ap[~(ap < 1e12)] = float("nan")
                self.plot.clear(); self.plot.plot(t, pe / 1e3, pen=pg.mkPen("#2aa9ff", width=2), name="perigee"); self.plot.plot(t, ap / 1e3, pen=pg.mkPen("#ff7a2a", width=2), name="apogee")

    def _dv(self): return tuple(s.value() for s in self.dv)

    def preview(self):
        w = self.W()
        if w: w.command("preview", *self._dv())

    def show_preview(self, out):
        b, a = out["before"], out["after"]
        def row(lbl, k, fmt): return f"<tr><td>{lbl}</td><td>{fmt(b[k])}</td><td>{fmt(a[k])}</td></tr>"
        km = lambda x: "inf" if x == float("inf") else f"{x / 1e3:,.1f} km"
        self.out.setHtml(f"<b>About {out['body']}</b><table cellspacing=6><tr><th></th><th>before</th><th>after</th></tr>" + row("Perigee alt", "peri_alt", km) + row("Apogee alt", "apo_alt", km)
                         + row("Semi-major axis", "a", km) + row("Eccentricity", "e", lambda x: f"{x:.4f}") + row("Inclination", "inc", lambda x: f"{x:.3f} deg")
                         + row("Period", "period", lambda x: "inf" if x == float("inf") else f"{x / 60:,.1f} min") + "</table>" + ("<b style='color:#f87171'>Escape trajectory</b>" if a["e"] >= 1 else ""))

    def predict(self):
        w = self.W()
        if w:
            T = self.snap["tm"]["period_s"] if self.snap and self.snap["tm"]["period_s"] != float("inf") else 3 * 3600.0
            w.command("predict", min(max(T * 1.05, 600.0), 3e7), 500, self._dv())

    def clear(self):
        w = self.W()
        if w: w.command("clear_prediction")

    def apply(self):
        w = self.W()
        if w: w.command("impulse", *self._dv())

    def hohmann(self):
        if not self.snap: return
        tm = self.snap["tm"]; sma = tm["sma_m"]
        if not (sma > 0 and sma < 1e15): self.hlabel.setText("Current orbit is not bound."); return
        body_r = sma - (tm["periapsis_alt_m"] + tm["apoapsis_alt_m"]) / 2.0
        r1 = sma; r2 = body_r + self.target.value() * 1e3; mu = -tm["specific_energy_jkg"] * 2 * sma
        h = hohmann(mu, r1, r2); self.dv[0].setValue(h["dv1"]); self.hlabel.setText(f"dv1 = {h['dv1']:,.1f} m/s now, then dv2 = {h['dv2']:,.1f} m/s at apogee after {h['tof'] / 60:,.1f} min  (total {h['total']:,.0f} m/s)")
