"""Telemetry workspace: live readouts, selectable graphs, run comparison, trajectory + 'travel to target' analytics."""
import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QComboBox, QPushButton, QTabWidget, QListWidget, QListWidgetItem,
                             QCheckBox, QGroupBox, QFileDialog, QProgressBar, QTextBrowser)
from astrax.recorder import UNITS, Recorder

pg.setConfigOptions(antialias=True, background="#0a0e13", foreground="#a9b6c6")
PALETTE = ["#2aa9ff", "#ff7a2a", "#34d399", "#fbbf24", "#c084fc", "#f87171", "#22d3ee", "#a3e635"]
# (key, label, scale divisor, display unit)
VARS = [("altitude_m", "Altitude", 1e3, "km"), ("speed_mps", "Velocity (vs dominant body)", 1.0, "m/s"), ("surface_speed_mps", "Surface-relative velocity", 1.0, "m/s"),
        ("accel_thrust_ms2", "Thrust acceleration", 1.0, "m/s^2"), ("g_load", "Thrust g-load", 1.0, "g"), ("propellant_kg", "Fuel mass", 1.0, "kg"), ("mass_kg", "Total mass", 1.0, "kg"),
        ("thrust_n", "Thrust", 1e3, "kN"), ("dynamic_pressure_pa", "Dynamic pressure", 1e3, "kPa"), ("total_energy_j", "Total energy (dominant body)", 1e9, "GJ"),
        ("specific_energy_jkg", "Specific orbital energy", 1e6, "MJ/kg"), ("kinetic_j", "Kinetic energy", 1e9, "GJ"), ("potential_j", "Potential energy", 1e9, "GJ"),
        ("dist_target_m", "Distance from destination", 1e3, "km"), ("dist_sun_m", "Distance from Sun", 1.495978707e11, "AU"),
        ("apoapsis_alt_m", "Apoapsis altitude", 1e3, "km"), ("periapsis_alt_m", "Periapsis altitude", 1e3, "km"), ("ecc", "Eccentricity", 1.0, ""),
        ("dv_spent_mps", "Delta-v spent", 1.0, "m/s"), ("gravity_force_dominant_n", "Gravitational force (dominant)", 1e3, "kN"),
        ("mach", "Mach number", 1.0, ""), ("aoa_deg", "Angle of attack", 1.0, "deg"), ("heat_flux_w_m2", "Nose heat flux", 1e3, "kW/m^2"),
        ("stress_mpa", "Peak skin stress", 1.0, "MPa"), ("drag_n", "Aerodynamic drag", 1e3, "kN"), ("axial_g", "Axial load factor", 1.0, "g"),
        ("latitude_deg", "Sub-point latitude", 1.0, "deg"), ("longitude_deg", "Sub-point longitude", 1.0, "deg")]


class TelemetryPanel(QWidget):
    def __init__(self):
        super().__init__(); v = QVBoxLayout(self); self.runs = []; self.rec = None
        self.tabs = QTabWidget(); v.addWidget(self.tabs)
        # ---- live readouts
        live = QWidget(); g = QGridLayout(live); self.val = {}
        items = [("MET", "met"), ("Status", "status"), ("Phase", "phase"), ("Stage", "stage"), ("Altitude", "alt"), ("Velocity", "vel"), ("Surface vel.", "svel"), ("Accel (thrust)", "acc"), ("Mass", "mass"),
                 ("Fuel", "fuel"), ("Thrust", "thr"), ("Dyn. pressure", "q"), ("Body", "body"), ("Apoapsis", "ap"), ("Periapsis", "pe"), ("Eccentricity", "ecc"), ("Inclination", "inc"),
                 ("Orbital energy", "en"), ("Gravity (dom.)", "grav"), ("To destination", "dest"), ("Delta-v spent", "dv")]
        for i, (lab, key) in enumerate(items):
            l = QLabel(lab); l.setObjectName("muted"); val = QLabel("-"); val.setObjectName("mono"); val.setStyleSheet("font-size: 12pt;")
            g.addWidget(l, i // 3 * 2, i % 3); g.addWidget(val, i // 3 * 2 + 1, i % 3); self.val[key] = val
        self.fuel_bar = QProgressBar(); self.fuel_bar.setFormat("Propellant %p%"); g.addWidget(self.fuel_bar, 20, 0, 1, 3); g.setRowStretch(30, 1)
        self.tabs.addTab(live, "Live")
        # ---- graphs
        gw = QWidget(); gv = QVBoxLayout(gw); row = QHBoxLayout(); self.combo = []
        for i, d in enumerate(("altitude_m", "speed_mps", "accel_thrust_ms2", "propellant_kg")):
            c = QComboBox()
            for k, lab, sc, u in VARS: c.addItem(f"{lab} [{u}]" if u else lab, k)
            c.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon); c.setMinimumContentsLength(10)
            c.setCurrentIndex([x[0] for x in VARS].index(d)); c.currentIndexChanged.connect(self.redraw); row.addWidget(c); self.combo.append(c)
        gv.addLayout(row); self.plots = []
        grid = QGridLayout(); gv.addLayout(grid, 1)
        for i in range(4):
            p = pg.PlotWidget(); p.setMinimumSize(120, 90); p.setDownsampling(auto=True, mode="peak"); p.setClipToView(True); p.showGrid(x=True, y=True, alpha=.25); p.addLegend(offset=(10, 10)); self.plots.append(p); grid.addWidget(p, i // 2, i % 2)
        row = QHBoxLayout(); self.cmp = QListWidget(); self.cmp.setMaximumHeight(80); self.cmp.setMinimumHeight(30); self.cmp.itemChanged.connect(self.redraw); row.addWidget(self.cmp, 1)
        col = QVBoxLayout()
        for txt, fn in (("Keep this run for comparison", self.keep_run), ("Clear saved runs", self.clear_runs), ("Export CSV...", self.export_csv),
                        ("Save session...", self.save_session), ("Load session...", self.load_session)):
            b = QPushButton(txt); b.clicked.connect(fn); col.addWidget(b)
        row.addLayout(col); gv.addLayout(row); self.tabs.addTab(gw, "Graphs")
        # ---- trajectory & travel analytics
        tw = QWidget(); tv = QVBoxLayout(tw); row = QHBoxLayout()
        self.traj_mode = QComboBox(); self.traj_mode.addItems(["Relative to launch/dominant body (X-Y)", "Heliocentric ecliptic (X-Y, AU)", "Distance from Sun & destination vs time", "Ground track (latitude / longitude)"])
        self.traj_mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon); self.traj_mode.setMinimumContentsLength(14); self.traj_mode.currentIndexChanged.connect(self.redraw_traj); row.addWidget(self.traj_mode); tv.addLayout(row)
        self.traj = pg.PlotWidget(); self.traj.setMinimumSize(120, 90); self.traj.setDownsampling(auto=True, mode="peak"); self.traj.showGrid(x=True, y=True, alpha=.25); self.traj.setAspectLocked(False); tv.addWidget(self.traj, 3)
        self.analysis = QTextBrowser(); self.analysis.setMaximumHeight(170); self.analysis.setMinimumHeight(40); tv.addWidget(self.analysis); self.tabs.addTab(tw, "Trajectory & travel analysis")
        self._tick = 0; self.target_name = "Moon"

    # ---------- live ----------
    def update_live(self, snap):
        tm = snap["tm"]; V = self.val
        V["met"].setText(f"T+{tm['met_s']:,.1f} s"); V["status"].setText(tm["status"]); V["phase"].setText(snap["phase"]); V["stage"].setText(tm["stage"])
        V["alt"].setText(f"{tm['altitude_m'] / 1e3:,.2f} km"); V["vel"].setText(f"{tm['speed_mps']:,.1f} m/s"); V["svel"].setText(f"{tm['surface_speed_mps']:,.1f} m/s")
        V["acc"].setText(f"{tm['accel_thrust_ms2']:.2f} m/s^2 ({tm['g_load']:.2f} g)"); V["mass"].setText(f"{tm['mass_kg']:,.0f} kg"); V["fuel"].setText(f"{tm['propellant_kg']:,.0f} kg")
        V["thr"].setText(f"{tm['thrust_n'] / 1e3:,.0f} kN"); V["q"].setText(f"{tm['dynamic_pressure_pa'] / 1e3:.2f} kPa"); V["body"].setText(tm["body"])
        ap = tm["apoapsis_alt_m"]; V["ap"].setText("escape" if ap == float("inf") else f"{ap / 1e3:,.1f} km"); V["pe"].setText(f"{tm['periapsis_alt_m'] / 1e3:,.1f} km")
        V["ecc"].setText(f"{tm['ecc']:.5f}"); V["inc"].setText(f"{tm['inc_deg']:.2f} deg"); V["en"].setText(f"{tm['specific_energy_jkg'] / 1e6:,.3f} MJ/kg")
        V["grav"].setText(f"{tm['gravity_force_dominant_n'] / 1e3:,.1f} kN"); V["dest"].setText(f"{tm['dist_target_m'] / 1e3:,.0f} km"); V["dv"].setText(f"{tm['dv_spent_mps']:,.0f} m/s")
        self.fuel_bar.setValue(int(100 * tm["propellant_fraction"]))
        self._tick += 1
        if self._tick % 15 == 0 and self.rec is not None and len(self.rec) > 1: self.redraw(); self.redraw_traj()

    # ---------- graphs ----------
    def set_recorder(self, rec, target): self.rec = rec; self.target_name = target

    def _xy(self, rec, key):
        """(time, scaled series) from ONE consistent snapshot."""
        sc = next(x for x in VARS if x[0] == key); t, a = rec.arrays("met_s", key); a = a / sc[2]; a[~np.isfinite(a)] = np.nan; return t, a

    def redraw(self, *_):
        if self.rec is None: return
        for p, c in zip(self.plots, self.combo):
            key = c.currentData(); sc = next(x for x in VARS if x[0] == key); p.clear(); p.setLabel("bottom", "Mission elapsed time", units="s"); p.setLabel("left", sc[1], units=sc[3])
            p.plot(*self._xy(self.rec, key), pen=pg.mkPen(PALETTE[0], width=2), name="current run")
            for i in range(self.cmp.count()):
                it = self.cmp.item(i)
                if it.checkState() == Qt.CheckState.Checked:
                    r = self.runs[i]; p.plot(*self._xy(r, key), pen=pg.mkPen(PALETTE[1 + i % 7], width=1.5, style=Qt.PenStyle.DashLine), name=it.text())

    def redraw_traj(self, *_):
        r = self.rec
        if r is None or len(r) < 2: return
        self.traj.clear(); m = self.traj_mode.currentIndex()
        if m == 0:
            x, y = r.arrays("rel_x", "rel_y"); x, y = x / 1e3, y / 1e3
            self.traj.setLabel("bottom", "x (ecliptic, relative to dominant body)", units="km"); self.traj.setLabel("left", "y", units="km"); self.traj.plot(x, y, pen=pg.mkPen("#fbbf24", width=2))
        elif m == 1:
            self.traj.setLabel("bottom", "x (ecliptic J2000)", units="AU"); self.traj.setLabel("left", "y", units="AU")
            x, y = r.arrays("rp_x", "rp_y"); self.traj.plot(x / 1.495978707e11, y / 1.495978707e11, pen=pg.mkPen("#fbbf24", width=2))
        elif m == 3:
            la, lo = r.arrays("latitude_deg", "longitude_deg"); self.traj.setLabel("bottom", "Longitude", units="deg"); self.traj.setLabel("left", "Latitude", units="deg"); self.traj.setXRange(-180, 180); self.traj.setYRange(-90, 90)
            lo = np.where(np.abs(np.diff(lo, prepend=lo[:1])) > 180, np.nan, lo); self.traj.plot(lo, la, pen=pg.mkPen("#34d399", width=2))
        else:
            self.traj.setLabel("bottom", "Mission elapsed time", units="s"); self.traj.setLabel("left", "Distance", units="AU / km (see legend)")
            self.traj.addLegend(); t, ds, dt_ = r.arrays("met_s", "dist_sun_m", "dist_target_m")
            self.traj.plot(t, ds / 1.495978707e11, pen=pg.mkPen("#ff7a2a", width=2), name="distance from Sun [AU]")
            self.traj.plot(t, dt_ / 1e9, pen=pg.mkPen("#2aa9ff", width=2), name=f"distance to {self.target_name} [x10^6 km]")
        self.analysis.setHtml(self.analyse())

    def analyse(self):
        r = self.rec; t, d, sun, alt = r.arrays("met_s", "dist_target_m", "dist_sun_m", "altitude_m")
        if len(t) < 2: return "Not enough data yet."
        i = int(np.nanargmin(d)); out = [f"<b>Travel analysis (from recorded simulation data, {len(r)} samples)</b>",
               f"Closest approach to <b>{self.target_name}</b> (surface): {d[i] / 1e3:,.0f} km at T+{t[i]:,.0f} s",
               f"Current distance to destination: {d[-1] / 1e3:,.0f} km; distance from Sun: {sun[-1] / 1.495978707e11:.4f} AU (min {np.nanmin(sun) / 1.495978707e11:.4f}, max {np.nanmax(sun) / 1.495978707e11:.4f} AU)"]
        if len(t) > 5 and t[-1] > t[-5]:
            rate = (d[-1] - d[-5]) / (t[-1] - t[-5])
            if rate < -1: out.append(f"Closing speed on destination: {-rate:,.1f} m/s - naive straight-line ETA {d[-1] / -rate / 86400:,.2f} days (ignores gravity & manoeuvres)")
            else: out.append(f"Receding from destination at {rate:,.1f} m/s")
        out.append(f"Max altitude above dominant body: {np.nanmax(alt) / 1e3:,.1f} km")
        return "<br>".join(out)

    # ---------- runs / files ----------
    def keep_run(self):
        if self.rec is None or not len(self.rec): return
        c = Recorder(); c.data = {k: list(v) for k, v in self.rec.data.items()}; c.labels = {k: list(v) for k, v in self.rec.labels.items()}
        self.runs.append(c); it = QListWidgetItem(f"run {len(self.runs)} ({len(c)} pts)"); it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable); it.setCheckState(Qt.CheckState.Checked); self.cmp.addItem(it)

    def clear_runs(self): self.runs.clear(); self.cmp.clear(); self.redraw()

    def export_csv(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export telemetry CSV", "telemetry.csv", "CSV (*.csv)")
        if p and self.rec: self.rec.export_csv(p)

    def save_session(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save simulation session", "session.astrax.json", "AstraX session (*.json)")
        if p and self.rec: self.rec.save_session(p)

    def load_session(self):
        p, _ = QFileDialog.getOpenFileName(self, "Load simulation session", "", "AstraX session (*.json)")
        if p:
            c = Recorder.load_session(p); self.runs.append(c); it = QListWidgetItem(p.split("/")[-1]); it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable); it.setCheckState(Qt.CheckState.Checked); self.cmp.addItem(it); self.redraw()
