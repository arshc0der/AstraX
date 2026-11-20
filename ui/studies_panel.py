"""Research studies: maximum payload, parameter sweep, Monte Carlo robustness, atmospheric re-entry calculator."""
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget, QComboBox, QDoubleSpinBox, QSpinBox, QPushButton, QLabel, QTextBrowser, QProgressBar, QTableWidget, QTableWidgetItem)
from astrax import studies, reentry
from ui.worker_util import FuncWorker

SWEEPABLE = ["payload_mass_kg", "cd", "stages[0].engine.count", "stages[0].engine.thrust_vac_n", "stages[0].propellant_kg", "stages[0].dry_mass_kg", "stages[0].wall_thickness_mm", "limits.max_q_pa", "nose_radius_m"]


class StudiesPanel(QWidget):
    def __init__(self, rocket_getter, system_getter):
        super().__init__(); self.R, self.S = rocket_getter, system_getter; v = QVBoxLayout(self); tabs = QTabWidget(); v.addWidget(tabs)
        self.bar = QProgressBar(); self.bar.setVisible(False); v.addWidget(self.bar); self.note = QLabel("Each ascent takes a few seconds; studies run in the background.", objectName="muted"); self.note.setWordWrap(True); v.addWidget(self.note)
        # ---- max payload
        t = QWidget(); tv = QVBoxLayout(t); tv.addWidget(QLabel("Largest payload your current design can put into a stable ~200 km orbit (bisection on payload mass).", objectName="muted"))
        self.b_pay = QPushButton("Find maximum payload"); self.b_pay.setObjectName("primary"); self.b_pay.clicked.connect(self.run_payload); tv.addWidget(self.b_pay); self.out_pay = QTextBrowser(); tv.addWidget(self.out_pay); tabs.addTab(t, "Max payload")
        # ---- sweep
        t = QWidget(); tv = QVBoxLayout(t); f = QFormLayout(); self.par = QComboBox(); self.par.setEditable(True); self.par.addItems(SWEEPABLE); f.addRow("Parameter", self.par)
        self.v0 = QDoubleSpinBox(); self.v0.setRange(-1e12, 1e12); self.v0.setDecimals(3); self.v0.setValue(2000); self.v1 = QDoubleSpinBox(); self.v1.setRange(-1e12, 1e12); self.v1.setDecimals(3); self.v1.setValue(14000)
        r = QHBoxLayout(); r.addWidget(self.v0); r.addWidget(self.v1); f.addRow("From / to", r); self.nst = QSpinBox(); self.nst.setRange(2, 40); self.nst.setValue(8); f.addRow("Steps", self.nst); tv.addLayout(f)
        self.b_sw = QPushButton("Run sweep"); self.b_sw.setObjectName("primary"); self.b_sw.clicked.connect(self.run_sweep); tv.addWidget(self.b_sw)
        self.sw_plot = pg.PlotWidget(); self.sw_plot.setMinimumHeight(110); self.sw_plot.showGrid(x=True, y=True, alpha=.25); self.sw_plot.addLegend(); tv.addWidget(self.sw_plot)
        self.sw_tab = QTableWidget(0, 5); self.sw_tab.setHorizontalHeaderLabels(["Value", "Verdict", "Perigee km", "Max-Q kPa", "Max g"]); self.sw_tab.horizontalHeader().setStretchLastSection(True); tv.addWidget(self.sw_tab); tabs.addTab(t, "Parameter sweep")
        # ---- monte carlo
        t = QWidget(); tv = QVBoxLayout(t); f = QFormLayout(); self.mc_n = QSpinBox(); self.mc_n.setRange(3, 200); self.mc_n.setValue(20); f.addRow("Runs", self.mc_n)
        self.mc_s = {}
        for k, lab, d in (("thrust", "Thrust sigma", 3.0), ("isp", "Isp sigma", 1.0), ("cd", "Drag coefficient sigma", 10.0), ("dry_mass", "Dry mass sigma", 3.0), ("propellant", "Propellant load sigma", 0.5)):
            s = QDoubleSpinBox(); s.setRange(0, 50); s.setValue(d); s.setSuffix(" %"); self.mc_s[k] = s; f.addRow(lab, s)
        tv.addLayout(f); self.b_mc = QPushButton("Run Monte Carlo"); self.b_mc.setObjectName("primary"); self.b_mc.clicked.connect(self.run_mc); tv.addWidget(self.b_mc); self.out_mc = QTextBrowser(); tv.addWidget(self.out_mc); tabs.addTab(t, "Monte Carlo")
        # ---- reentry
        t = QWidget(); tv = QVBoxLayout(t); f = QFormLayout(); self.re_body = QComboBox(); self.re_body.addItems(["Earth", "Mars", "Venus"]); f.addRow("Body", self.re_body); self.re = {}
        for k, lab, val, lo, hi, suf in (("m", "Mass", 5000, 1, 1e6, " kg"), ("cd", "Drag coefficient", 1.3, 0.1, 3, ""), ("A", "Reference area", 12, 0.01, 500, " m2"), ("rn", "Nose radius", 4.7, 0.01, 20, " m"),
                                         ("v", "Entry speed", 7800, 500, 20000, " m/s"), ("g", "Flight-path angle (below horizon)", 2.0, 0.1, 90, " deg")):
            s = QDoubleSpinBox(); s.setRange(lo, hi); s.setValue(val); s.setSuffix(suf); s.setDecimals(2); self.re[k] = s; f.addRow(lab, s)
        tv.addLayout(f); b = QPushButton("Compute entry"); b.setObjectName("primary"); b.clicked.connect(self.run_reentry); tv.addWidget(b); self.re_plot = pg.PlotWidget(); self.re_plot.setMinimumHeight(110); self.re_plot.showGrid(x=True, y=True, alpha=.25); tv.addWidget(self.re_plot)
        self.out_re = QTextBrowser(); self.out_re.setMaximumHeight(120); tv.addWidget(self.out_re); tabs.addTab(t, "Re-entry")

    def _run(self, fn, *args, done, buttons=(), **kw):
        for b in buttons: b.setEnabled(False)
        self.bar.setVisible(True); self.bar.setRange(0, 100); self.w = FuncWorker(fn, *args, **kw)
        self.w.progress.connect(lambda i, n, t: (self.bar.setValue(int(100 * i / max(n, 1))), self.note.setText(t))); fin = lambda: (self.bar.setVisible(False), [b.setEnabled(True) for b in buttons])
        self.w.done.connect(lambda r: (fin(), done(r))); self.w.failed.connect(lambda m: (fin(), self.note.setText("Failed: " + m))); self.w.start()

    def run_payload(self): self._run(studies.max_payload_to_orbit, self.R(), self.S(), done=lambda r: self.out_pay.setHtml(f"<h3>Maximum payload: {r['max_payload_kg']:,.0f} kg</h3><p>{r['note']}</p><p><i>Estimate: survival is not strictly monotonic in payload mass.</i></p>"), buttons=(self.b_pay,))

    def run_sweep(self):
        vals = np.linspace(self.v0.value(), self.v1.value(), self.nst.value())
        if "count" in self.par.currentText() or "stages" in self.par.currentText() and "count" in self.par.currentText(): vals = np.unique(np.round(vals)).astype(int)
        self._run(studies.sweep, self.R(), self.par.currentText(), list(vals), self.S(), done=self._sweep_done, buttons=(self.b_sw,))

    def _sweep_done(self, rows):
        self.sw_tab.setRowCount(len(rows)); x = [r["value"] for r in rows]
        for i, r in enumerate(rows):
            for j, val in enumerate([f"{r['value']:g}", r["verdict"], f"{r['peri_km']:.0f}", f"{r['max_q_kpa']:.1f}", f"{r['max_g']:.1f}"]): self.sw_tab.setItem(i, j, QTableWidgetItem(val))
        self.sw_plot.clear(); self.sw_plot.plot(x, [r["peri_km"] if np.isfinite(r["peri_km"]) else 0 for r in rows], pen=pg.mkPen("#2aa9ff", width=2), symbol="o", name="perigee [km]")
        self.sw_plot.plot(x, [r["max_q_kpa"] for r in rows], pen=pg.mkPen("#ff7a2a", width=2), symbol="t", name="max-Q [kPa]"); self.sw_plot.setLabel("bottom", self.par.currentText())

    def run_mc(self):
        sg = {k: s.value() / 100 for k, s in self.mc_s.items()}
        self._run(studies.monte_carlo, self.R(), self.mc_n.value(), 1, self.S(), sg, done=lambda r: self.out_mc.setHtml(f"<h3>Success rate: {r['success_rate'] * 100:.0f}% ({r['n']} runs)</h3>" + "<br>".join(f"{k}: {v}" for k, v in r["verdicts"].items()) + "<p><i>Random perturbations (1-sigma): " + ", ".join(f"{k} {v * 100:g}%" for k, v in r["sigma"].items()) + "</i></p>"), buttons=(self.b_mc,))

    def run_reentry(self):
        b = self.S().get(self.re_body.currentText()); p = {k: s.value() for k, s in self.re.items()}
        r = reentry.entry(b, p["m"], p["cd"], p["A"], p["rn"], p["v"], p["g"])
        self.re_plot.clear(); self.re_plot.setLabel("bottom", "Downrange", units="m"); self.re_plot.setLabel("left", "Altitude", units="m")
        if len(r.path): self.re_plot.plot(r.path[:, 0], r.path[:, 1], pen=pg.mkPen("#fbbf24", width=2))
        self.out_re.setHtml(f"Peak deceleration <b>{r.peak_decel_g:.1f} g</b> at {r.peak_decel_alt_m / 1e3:.0f} km<br>Peak stagnation heat flux <b>{r.peak_heat_flux_w_m2 / 1e3:,.0f} kW/m2</b> at {r.peak_heat_alt_m / 1e3:.0f} km; heat load {r.heat_load_j_m2 / 1e6:.0f} MJ/m2<br>"
                            f"{'Reached the surface at ' + format(r.impact_speed_mps, '.0f') + ' m/s' if r.reached_surface else 'Did not reach the surface (skip-out or slowed to a stop)'} after {r.duration_s:.0f} s<br><i>Ballistic, non-rotating atmosphere, validated against Allen-Eggers.</i>")
