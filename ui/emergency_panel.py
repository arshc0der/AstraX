"""Flight safety panel: live load gauges vs design limits, failure injection, abort."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QProgressBar, QLabel, QDoubleSpinBox, QCheckBox, QComboBox, QFormLayout)


class Gauge(QWidget):
    def __init__(self, label, tip=""):
        super().__init__(); h = QHBoxLayout(self); h.setContentsMargins(0, 0, 0, 0); l = QLabel(label); l.setMinimumWidth(150); l.setToolTip(tip); h.addWidget(l)
        self.bar = QProgressBar(); self.bar.setRange(0, 150); self.bar.setFormat("%v%"); self.bar.setToolTip(tip); h.addWidget(self.bar, 1)

    def set(self, ratio):
        v = int(max(0, min(150, ratio * 100))); self.bar.setValue(v)
        col = "#34d399" if ratio < 0.7 else "#fbbf24" if ratio < 1.0 else "#f87171"
        self.bar.setStyleSheet(f"QProgressBar::chunk {{ background: {col}; }}")


class EmergencyPanel(QWidget):
    def __init__(self, worker_getter, cfg_getter):
        super().__init__(); self.W, self.C = worker_getter, cfg_getter; v = QVBoxLayout(self)
        g = QGroupBox("Loads vs design limits (100% = limit)"); gv = QVBoxLayout(g)
        self.gq = Gauge("Dynamic pressure", "Max-Q vs the design limit set in the Rocket designer"); self.gg = Gauge("Axial acceleration", "Axial load factor in g")
        self.gh = Gauge("Nose heating", "Sutton-Graves stagnation heat flux"); self.gs = Gauge("Structural stress", "Combined axial+bending stress vs allowable (yield / factor of safety)")
        for x in (self.gq, self.gg, self.gh, self.gs): gv.addWidget(x)
        self.status = QLabel("Systems nominal"); self.status.setWordWrap(True); self.status.setStyleSheet("font-weight: 700;"); gv.addWidget(self.status); v.addWidget(g)
        g = QGroupBox("Emergency actions"); gv = QVBoxLayout(g)
        self.abort = QPushButton("ABORT  (jettison stages, parachute capsule)"); self.abort.setObjectName("danger"); self.abort.setToolTip("Cuts engines, separates every stage and sends the payload capsule down on a parachute"); self.abort.clicked.connect(lambda: self._cmd("abort")); gv.addWidget(self.abort)
        b = QPushButton("Engine cutoff"); b.clicked.connect(lambda: self._cmd("engine_cutoff")); gv.addWidget(b); v.addWidget(g)
        g = QGroupBox("Failure injection (what-if testing)"); f = QFormLayout(g)
        b = QPushButton("Engine out (-1 engine, lowest stage)"); b.clicked.connect(lambda: self._cmd("engine_out")); f.addRow(b)
        self.leak = QDoubleSpinBox(); self.leak.setRange(1, 1e5); self.leak.setValue(300); self.leak.setSuffix(" kg/s"); b = QPushButton("Start propellant leak"); b.clicked.connect(lambda: self._cmd("fuel_leak", self.leak.value())); r = QHBoxLayout(); r.addWidget(self.leak); r.addWidget(b); f.addRow(r)
        self.stuck = QDoubleSpinBox(); self.stuck.setRange(0, 1); self.stuck.setSingleStep(0.05); self.stuck.setValue(1.0); b = QPushButton("Throttle stuck at"); b.clicked.connect(lambda: self._cmd("stuck_throttle", self.stuck.value())); r = QHBoxLayout(); r.addWidget(b); r.addWidget(self.stuck); f.addRow(r)
        b = QPushButton("Guidance lost (attitude frozen)"); b.clicked.connect(lambda: self._cmd("guidance_loss")); f.addRow(b)
        b = QPushButton("Clear all faults"); b.clicked.connect(lambda: self._cmd("clear")); f.addRow(b); v.addWidget(g)
        g = QGroupBox("Simulation realism options"); f = QFormLayout(g)
        self.aero = QComboBox(); self.aero.addItems(["advanced", "simple"]); self.aero.setToolTip("advanced: Cd(Mach) + angle-of-attack normal force; simple: constant Cd, no lift"); self.aero.currentTextChanged.connect(lambda t: setattr(self.C(), "aero", t)); f.addRow("Aerodynamics", self.aero)
        self.prot = QCheckBox("Autopilot load protection"); self.prot.setChecked(True); self.prot.toggled.connect(lambda c: setattr(self.C(), "protect", c)); f.addRow(self.prot)
        self.fail = QCheckBox("Structural / thermal / control failures destroy the vehicle"); self.fail.setChecked(True); self.fail.toggled.connect(lambda c: setattr(self.C(), "failures", c)); f.addRow(self.fail)
        v.addWidget(g); v.addStretch(1)

    def _cmd(self, name, val=None):
        w = self.W()
        if w: w.command("emergency", name, val) if val is not None else w.command("emergency", name)

    def update_snapshot(self, snap):
        tm = snap["tm"]; self.gq.set(tm["q_ratio"]); self.gg.set(tm["g_ratio"]); self.gh.set(tm["heat_ratio"]); self.gs.set(tm["stress_ratio"])
        if tm["failure_reason"]: self.status.setText(f"VEHICLE LOST: {tm['failure_reason']}"); self.status.setStyleSheet("font-weight: 700; color: #f87171;")
        else:
            f = tm["faults"]; self.status.setText("Systems nominal" if f == "nominal" else f"FAULTS: {f}"); self.status.setStyleSheet(f"font-weight: 700; color: {'#34d399' if f == 'nominal' else '#fbbf24'};")

