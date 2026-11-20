"""Mission control: launch conditions, flight plan editor, presets, and the Python flight computer."""
import json
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHBoxLayout, QPlainTextEdit, QLabel, QTabWidget, QSpinBox, QMessageBox)
from astrax.simulation import LaunchConfig, Phase
from astrax.missions import PRESETS

MODES = ["fixed_local", "pitch_program", "gravity_turn", "ascent_hold", "powered_landing", "prograde", "retrograde", "radial_out", "radial_in", "normal", "antinormal", "coast", "hold"]
EXAMPLE_SCRIPT = '''# Flight computer - runs every physics step while "Script control" is on.
# API: rocket.set_thrust(0..1)  rocket.set_pitch(deg, 90=up)  rocket.set_heading(deg, 90=east)
#      rocket.get_altitude() [km]  rocket.get_velocity() [m/s]  rocket.stage()  rocket.log("text")
def mission_loop():
    alt_km = rocket.get_altitude()
    vel = rocket.get_velocity()
    if alt_km < 10:
        rocket.set_pitch(90); rocket.set_thrust(1.0)
    elif alt_km < 100:
        rocket.set_pitch(60); rocket.set_thrust(1.0)
    elif vel < 7600:
        rocket.set_pitch(0); rocket.set_thrust(1.0)
    else:
        rocket.set_thrust(0.0)
'''


class MissionPanel(QWidget):
    scenario_applied = pyqtSignal(object, object)     # LaunchConfig, plan
    script_requested = pyqtSignal(str, bool)
    preset_loaded = pyqtSignal(str)

    def __init__(self, body_names):
        super().__init__(); v = QVBoxLayout(self); tabs = QTabWidget(); v.addWidget(tabs)
        # --- launch / scenario ---
        t = QWidget(); tv = QVBoxLayout(t)
        self.preset = QComboBox(); self.preset.addItems(PRESETS.keys()); self.preset.setToolTip("Mission scenarios (editable afterwards)")
        b = QPushButton("Load scenario preset"); b.clicked.connect(self._load_preset); tv.addWidget(self.preset); tv.addWidget(b)
        g = QGroupBox("Launch conditions"); f = QFormLayout(g)
        self.body = QComboBox(); self.body.addItems(body_names); self.body.setCurrentText("Earth"); f.addRow("Launch body", self.body)
        self.target = QComboBox(); self.target.addItems(body_names); self.target.setCurrentText("Moon"); f.addRow("Destination body", self.target)
        self.mode = QComboBox(); self.mode.addItems(["pad", "orbit", "hover", "transfer"]); self.mode.setToolTip("pad: on the surface; orbit: circular parking orbit; hover: at rest above the surface (landing tests); transfer: interplanetary departure leg"); f.addRow("Start", self.mode)
        self.lat = QDoubleSpinBox(); self.lat.setRange(-90, 90); self.lat.setValue(28.5); self.lat.setSuffix(" deg"); f.addRow("Latitude", self.lat)
        self.lon = QDoubleSpinBox(); self.lon.setRange(-180, 180); self.lon.setValue(-80.6); self.lon.setSuffix(" deg"); f.addRow("Longitude", self.lon)
        self.hdg = QDoubleSpinBox(); self.hdg.setRange(0, 360); self.hdg.setValue(90); self.hdg.setSuffix(" deg"); self.hdg.setToolTip("Launch azimuth: 0=north, 90=east"); f.addRow("Launch direction", self.hdg)
        self.alt = QDoubleSpinBox(); self.alt.setRange(0, 1e7); self.alt.setValue(300); self.alt.setSuffix(" km"); self.alt.setToolTip("Altitude for orbit/hover starts; distance from body centre for transfer starts"); f.addRow("Start altitude / distance", self.alt)
        self.day = QDoubleSpinBox(); self.day.setRange(-1e5, 1e6); self.day.setSuffix(" d after J2000"); f.addRow("Start epoch", self.day)
        self.dvx = [QDoubleSpinBox() for _ in range(3)]
        for s, n in zip(self.dvx, "XYZ"): s.setRange(-1e5, 1e5); s.setSuffix(" m/s"); f.addRow(f"Extra initial velocity {n} (ecliptic)", s)
        tv.addWidget(g); tv.addStretch(1); tabs.addTab(t, "Launch")
        # --- flight plan ---
        t = QWidget(); pv = QVBoxLayout(t)
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["Name", "Mode", "Throttle", "Pitch", "Heading", "Ref", "Ends when (JSON)"])
        self.table.horizontalHeader().setStretchLastSection(True); pv.addWidget(self.table)
        row = QHBoxLayout()
        for txt, fn in (("Add phase", self.add_phase), ("Remove", self.remove_phase), ("Apply to simulation", self.apply)):
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
            if txt.startswith("Apply"): b.setObjectName("primary")
        pv.addLayout(row)
        pv.addWidget(QLabel("Modes: fixed_local, pitch_program (table in JSON key 'pitch_table' is set via presets), gravity_turn, ascent_hold, prograde/retrograde (Ref = body or 'dominant'), coast...", objectName="muted"))
        tabs.addTab(t, "Flight plan")
        # --- script ---
        t = QWidget(); sv = QVBoxLayout(t); self.script = QPlainTextEdit(EXAMPLE_SCRIPT); sv.addWidget(self.script)
        row = QHBoxLayout(); b = QPushButton("Enable script control"); b.setObjectName("primary"); b.clicked.connect(lambda: self.script_requested.emit(self.script.toPlainText(), True)); row.addWidget(b)
        b = QPushButton("Disable"); b.clicked.connect(lambda: self.script_requested.emit("", False)); row.addWidget(b); sv.addLayout(row)
        tabs.addTab(t, "Flight computer (Python)")
        self.plan = []; self._load_preset()

    def _fill_table(self):
        self.table.setRowCount(len(self.plan))
        for i, p in enumerate(self.plan):
            for j, val in enumerate([p.name, p.mode, f"{p.throttle:g}", f"{p.pitch_deg:g}", f"{p.heading_deg:g}", p.ref, json.dumps(p.until)]):
                self.table.setItem(i, j, QTableWidgetItem(val))

    def add_phase(self): self.plan.append(Phase("New phase", "prograde", 1.0, until={"duration_s": 60})); self._fill_table()
    def remove_phase(self):
        r = self.table.currentRow()
        if 0 <= r < len(self.plan): del self.plan[r]; self._fill_table()

    def _read_table(self):
        out = []
        for i in range(self.table.rowCount()):
            g = lambda j: self.table.item(i, j).text()
            old = self.plan[i] if i < len(self.plan) else Phase()
            out.append(Phase(g(0), g(1), float(g(2)), float(g(3)), float(g(4)), old.pitch_table, g(5), old.target_alt_m, json.loads(g(6) or "{}"), old.q_limit_pa))
        return out

    def launch_config(self):
        return LaunchConfig(body=self.body.currentText(), lat_deg=self.lat.value(), lon_deg=self.lon.value(), start_mode=self.mode.currentText(), orbit_altitude_m=self.alt.value() * 1000,
                            heading_deg=self.hdg.value(), target_body=self.target.currentText(), extra_velocity_mps=tuple(s.value() for s in self.dvx), start_day=self.day.value())

    def _load_preset(self):
        L, plan = PRESETS[self.preset.currentText()](); self.plan = plan; self._set_launch(L); self._fill_table()
        self.preset_loaded.emit(self.preset.currentText()); self.scenario_applied.emit(L, plan)

    def _set_launch(self, L):
        self.body.setCurrentText(L.body); self.target.setCurrentText(L.target_body); self.mode.setCurrentText(L.start_mode); self.lat.setValue(L.lat_deg); self.lon.setValue(L.lon_deg)
        self.hdg.setValue(L.heading_deg); self.alt.setValue(L.orbit_altitude_m / 1000); self.day.setValue(L.start_day)
        for s, v in zip(self.dvx, L.extra_velocity_mps): s.setValue(v)

    def apply(self):
        try: self.plan = self._read_table()
        except Exception as ex: QMessageBox.warning(self, "Invalid flight plan", str(ex)); return
        self.scenario_applied.emit(self.launch_config(), self.plan)

    def set_scenario(self, L, plan):
        self.plan = plan; self._set_launch(L); self._fill_table()
