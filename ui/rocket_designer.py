"""Rocket design workspace: stage list, property editors, live 3D preview, calculated estimates."""
import copy, math
import numpy as np
import pyqtgraph.opengl as gl
from pyqtgraph import Vector
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QListWidget, QPushButton, QDoubleSpinBox, QSpinBox,
                             QComboBox, QLineEdit, QLabel, QGroupBox, QScrollArea, QFileDialog, QMessageBox, QSplitter, QTableWidget,
                             QTableWidgetItem, QColorDialog, QCheckBox)
from astrax.rocket import Rocket, Stage, Engine, Nose, default_rocket
from astrax.rocket_mesh import build_rocket_parts, export_obj, load_obj
from ui.viewport import _merge


def dspin(lo, hi, val, dec=2, suffix="", step=None, tip=""):
    s = QDoubleSpinBox(); s.setRange(lo, hi); s.setDecimals(dec); s.setValue(val); s.setSuffix(suffix); s.setToolTip(tip)
    s.setGroupSeparatorShown(True); s.setKeyboardTracking(False)
    if step: s.setSingleStep(step)
    return s


class RocketDesigner(QWidget):
    rocket_changed = pyqtSignal(object)       # emitted on every edit (live)
    use_in_simulation = pyqtSignal(object)

    def __init__(self, rocket=None):
        super().__init__(); self.rocket = copy.deepcopy(rocket or default_rocket()); self._loading = False
        root = QHBoxLayout(self); split = QSplitter(); root.addWidget(split)
        # --- left: structure ---
        left = QWidget(); lv = QVBoxLayout(left)
        lv.addWidget(QLabel("VEHICLE STRUCTURE", objectName="h1"))
        self.name_edit = QLineEdit(self.rocket.name); self.name_edit.textChanged.connect(self._global_changed); lv.addWidget(self.name_edit)
        self.list = QListWidget(); self.list.currentRowChanged.connect(self._select); lv.addWidget(self.list, 1)
        row = QHBoxLayout()
        for txt, fn, tip in (("+ Stage", lambda: self.add_stage("core"), "Add a new core stage on top of the stack"),
                             ("+ Booster", lambda: self.add_stage("booster"), "Add strap-on boosters"),
                             ("Duplicate", self.duplicate, "Copy the selected stage"), ("Remove", self.remove, "Delete selected stage")):
            b = QPushButton(txt); b.setToolTip(tip); b.clicked.connect(fn); row.addWidget(b)
        lv.addLayout(row)
        row = QHBoxLayout()
        for txt, fn in (("Up", lambda: self.move(-1)), ("Down", lambda: self.move(1))):
            b = QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        lv.addLayout(row)
        io = QGroupBox("Files"); iv = QVBoxLayout(io)
        for txt, fn, tip in (("Save design (JSON)...", self.save, ""), ("Load design (JSON)...", self.load, ""),
                             ("Import custom 3D model (OBJ)...", self.import_obj, "Replaces the default look with your own mesh (display only; physics uses the numbers)"),
                             ("Export rocket as OBJ...", self.export_obj, "Open the generated rocket in Blender or any 3D tool")):
            b = QPushButton(txt); b.setToolTip(tip); b.clicked.connect(fn); iv.addWidget(b)
        lv.addWidget(io)
        use = QPushButton("Use this rocket in simulation"); use.setObjectName("primary"); use.clicked.connect(lambda: self.use_in_simulation.emit(copy.deepcopy(self.rocket))); lv.addWidget(use)
        split.addWidget(left)
        # --- centre: preview ---
        mid = QWidget(); mv = QVBoxLayout(mid)
        self.view = gl.GLViewWidget(); self.view.setBackgroundColor(QColor(8, 12, 18)); mv.addWidget(self.view, 1)
        self.mesh = None; g = gl.GLGridItem(); g.setSize(60, 60); g.setSpacing(5, 5); self.view.addItem(g)
        self.est_table = QTableWidget(0, 2); self.est_table.setHorizontalHeaderLabels(["Quantity (ESTIMATE)", "Value"]); self.est_table.horizontalHeader().setStretchLastSection(True)
        self.est_table.setMaximumHeight(250); self.est_table.verticalHeader().setVisible(False); mv.addWidget(self.est_table)
        self.warn = QLabel(""); self.warn.setWordWrap(True); mv.addWidget(self.warn)
        split.addWidget(mid)
        # --- right: editor ---
        sc = QScrollArea(); sc.setWidgetResizable(True); self.editor = QWidget(); self.ev = QVBoxLayout(self.editor); sc.setWidget(self.editor); split.addWidget(sc)
        self._build_editor(); split.setSizes([280, 760, 420])
        self._refresh_list(); self.list.setCurrentRow(0); self._changed()

    # ---------------- editor widgets ----------------
    def _build_editor(self):
        g = QGroupBox("Vehicle"); f = QFormLayout(g)
        self.w_payload = dspin(0, 5e6, self.rocket.payload_mass_kg, 1, " kg", 100, "Payload mass above the last stage"); f.addRow("Payload mass", self.w_payload)
        self.w_cd = dspin(0.01, 3, self.rocket.cd, 3, "", 0.01, "Reference drag coefficient (constant; Mach dependence not modelled)"); f.addRow("Drag coefficient Cd", self.w_cd)
        self.lbl_area = QLabel(); f.addRow("Cross-section area", self.lbl_area)
        self.nose_shape = QComboBox(); self.nose_shape.addItems(["ogive", "conic", "parabolic", "elliptical", "von_karman"]); f.addRow("Nose shape", self.nose_shape)
        self.nose_len = dspin(0.5, 60, 6, 2, " m"); f.addRow("Nose length", self.nose_len)
        self.nose_mass = dspin(0, 1e5, 0, 1, " kg", 50, "Fairing mass (jettison not modelled; counted as payload side mass)"); f.addRow("Nose/fairing mass", self.nose_mass)
        self.ev.addWidget(g)
        g = QGroupBox("Selected stage"); f = QFormLayout(g); self.stage_group = g
        self.s_name = QLineEdit(); f.addRow("Name", self.s_name)
        self.s_diam = dspin(0.2, 30, 3, 2, " m"); f.addRow("Diameter", self.s_diam)
        self.s_len = dspin(0.5, 200, 20, 2, " m"); f.addRow("Length (tank section)", self.s_len)
        self.s_inter = dspin(0, 20, 1, 2, " m"); f.addRow("Interstage length", self.s_inter)
        self.s_dry = dspin(1, 5e7, 5000, 1, " kg", 100); f.addRow("Dry mass", self.s_dry)
        self.s_prop = dspin(0, 5e8, 50000, 1, " kg", 1000, "Propellant loaded at launch"); f.addRow("Fuel mass (loaded)", self.s_prop)
        self.s_cap = dspin(0, 5e8, 50000, 1, " kg", 1000, "Maximum tank capacity (0 = same as loaded)"); f.addRow("Max fuel capacity", self.s_cap)
        self.s_count = QSpinBox(); self.s_count.setRange(1, 99); f.addRow("Booster copies", self.s_count)
        self.s_sep = QComboBox(); self.s_sep.addItems(["burnout", "time", "manual"]); self.s_sep.setToolTip("When this stage separates"); f.addRow("Separation", self.s_sep)
        self.s_septime = dspin(0, 1e5, 0, 1, " s"); f.addRow("Separation time (MET)", self.s_septime)
        self.s_color = QPushButton("Pick colour"); self.s_color.clicked.connect(self._pick_color); f.addRow("Colour", self.s_color)
        self.ev.addWidget(g)
        g = QGroupBox("Engines"); f = QFormLayout(g)
        self.e_count = QSpinBox(); self.e_count.setRange(1, 60); f.addRow("Number of engines", self.e_count)
        self.e_place = QComboBox(); self.e_place.addItems(["single", "ring", "octaweb", "cluster"]); f.addRow("Placement", self.e_place)
        self.e_thr = dspin(1e3, 1e8, 1e5, 0, " N", 10000, "Vacuum thrust of ONE engine"); f.addRow("Thrust (vac, each)", self.e_thr)
        self.e_isp_v = dspin(50, 1000, 300, 1, " s"); f.addRow("Isp (vacuum)", self.e_isp_v)
        self.e_isp_s = dspin(50, 1000, 270, 1, " s"); f.addRow("Isp (sea level)", self.e_isp_s)
        self.lbl_mdot = QLabel(); f.addRow("Fuel consumption", self.lbl_mdot)
        self.e_nd = dspin(0.1, 10, 0.8, 2, " m"); f.addRow("Nozzle diameter", self.e_nd)
        self.e_nl = dspin(0.1, 15, 1.2, 2, " m"); f.addRow("Nozzle length", self.e_nl)
        self.ev.addWidget(g)
        g = QGroupBox("Fins & landing legs"); f = QFormLayout(g)
        self.f_n = QSpinBox(); self.f_n.setRange(0, 12); f.addRow("Fins", self.f_n)
        self.f_span = dspin(0.1, 20, 1.5, 2, " m"); f.addRow("Fin span", self.f_span)
        self.f_root = dspin(0.1, 30, 2.5, 2, " m"); f.addRow("Root chord", self.f_root)
        self.f_tip = dspin(0.05, 30, 1.0, 2, " m"); f.addRow("Tip chord", self.f_tip)
        self.l_n = QSpinBox(); self.l_n.setRange(0, 8); f.addRow("Landing legs", self.l_n)
        self.l_len = dspin(0.5, 30, 6, 2, " m"); f.addRow("Leg length", self.l_len)
        self.ev.addWidget(g); self.ev.addStretch(1)
        for w in (self.w_payload, self.w_cd, self.nose_len, self.nose_mass): w.valueChanged.connect(self._global_changed)
        self.nose_shape.currentTextChanged.connect(self._global_changed)
        for w in (self.s_diam, self.s_len, self.s_inter, self.s_dry, self.s_prop, self.s_cap, self.s_count, self.s_septime, self.e_count, self.e_thr, self.e_isp_v, self.e_isp_s,
                  self.e_nd, self.e_nl, self.f_n, self.f_span, self.f_root, self.f_tip, self.l_n, self.l_len): w.valueChanged.connect(self._stage_changed)
        for w in (self.s_sep, self.e_place): w.currentTextChanged.connect(self._stage_changed)
        self.s_name.textChanged.connect(self._stage_changed)

    # ---------------- model <-> widgets ----------------
    def _cur(self):
        r = self.list.currentRow(); return self.rocket.stages[r] if 0 <= r < len(self.rocket.stages) else None

    def _refresh_list(self):
        r = self.list.currentRow(); self.list.blockSignals(True); self.list.clear()
        for s in self.rocket.stages:
            self.list.addItem(f"{'[B] ' if s.kind == 'booster' else ''}{s.name}  -  {s.engine.count}x {s.engine.thrust_vac_n / 1e3:,.0f} kN")
        self.list.blockSignals(False); self.list.setCurrentRow(min(max(r, 0), len(self.rocket.stages) - 1))

    def _select(self, row):
        s = self._cur()
        if s is None: return
        self._loading = True
        self.s_name.setText(s.name); self.s_diam.setValue(s.diameter_m); self.s_len.setValue(s.length_m); self.s_inter.setValue(s.interstage_length_m)
        self.s_dry.setValue(s.dry_mass_kg); self.s_prop.setValue(s.propellant_kg); self.s_cap.setValue(s.propellant_capacity_kg)
        self.s_count.setValue(s.booster_count); self.s_count.setEnabled(s.kind == "booster"); self.s_sep.setCurrentText(s.separation); self.s_septime.setValue(s.separation_time_s)
        e = s.engine; self.e_count.setValue(e.count); self.e_place.setCurrentText(e.placement); self.e_thr.setValue(e.thrust_vac_n); self.e_isp_v.setValue(e.isp_vac_s); self.e_isp_s.setValue(e.isp_sl_s)
        self.e_nd.setValue(e.nozzle_diameter_m); self.e_nl.setValue(e.nozzle_length_m)
        self.f_n.setValue(s.fin_count); self.f_span.setValue(s.fin_span_m); self.f_root.setValue(s.fin_root_chord_m); self.f_tip.setValue(s.fin_tip_chord_m)
        self.l_n.setValue(s.leg_count); self.l_len.setValue(s.leg_length_m); self._loading = False; self._update_labels()

    def _stage_changed(self, *_):
        s = self._cur()
        if s is None or self._loading: return
        s.name = self.s_name.text(); s.diameter_m = self.s_diam.value(); s.length_m = self.s_len.value(); s.interstage_length_m = self.s_inter.value()
        s.dry_mass_kg = self.s_dry.value(); s.propellant_kg = self.s_prop.value(); s.propellant_capacity_kg = self.s_cap.value(); s.booster_count = self.s_count.value()
        s.separation = self.s_sep.currentText(); s.separation_time_s = self.s_septime.value()
        e = s.engine; e.count = self.e_count.value(); e.placement = self.e_place.currentText(); e.thrust_vac_n = self.e_thr.value(); e.isp_vac_s = self.e_isp_v.value(); e.isp_sl_s = self.e_isp_s.value()
        e.nozzle_diameter_m = self.e_nd.value(); e.nozzle_length_m = self.e_nl.value()
        s.fin_count = self.f_n.value(); s.fin_span_m = self.f_span.value(); s.fin_root_chord_m = self.f_root.value(); s.fin_tip_chord_m = self.f_tip.value()
        s.leg_count = self.l_n.value(); s.leg_length_m = self.l_len.value()
        self.nose_changed_diameter(); self._changed(rebuild_list=True)

    def nose_changed_diameter(self):
        cores = self.rocket.cores
        if cores: self.rocket.nose.base_diameter_m = cores[-1].diameter_m

    def _global_changed(self, *_):
        if self._loading: return
        r = self.rocket; r.name = self.name_edit.text(); r.payload_mass_kg = self.w_payload.value(); r.cd = self.w_cd.value()
        r.nose.shape = self.nose_shape.currentText(); r.nose.length_m = self.nose_len.value(); r.nose.mass_kg = self.nose_mass.value()
        self._changed()

    def _pick_color(self):
        s = self._cur()
        if s is None: return
        c = QColorDialog.getColor(QColor.fromRgbF(*s.color))
        if c.isValid(): s.color = (c.redF(), c.greenF(), c.blueF(), 1.0); self._changed()

    def _update_labels(self):
        s = self._cur()
        self.lbl_area.setText(f"{self.rocket.reference_area_m2:.2f} m^2  (from diameter)")
        if s: self.lbl_mdot.setText(f"{s.engine.mdot:,.1f} kg/s total (derived from thrust & Isp)")

    def _changed(self, rebuild_list=False):
        if rebuild_list: self._refresh_list()
        self._update_labels(); self._rebuild_mesh(); self._update_estimates(); self.rocket_changed.emit(self.rocket)

    def _rebuild_mesh(self):
        V, F, C = _merge(build_rocket_parts(self.rocket))
        if self.mesh is not None: self.view.removeItem(self.mesh)
        self.mesh = gl.GLMeshItem(vertexes=V, faces=F, faceColors=C, smooth=False, shader="shaded"); self.view.addItem(self.mesh)
        h = self.rocket.total_height_m; self.view.opts["center"] = Vector(0, 0, h / 2); self.view.setCameraPosition(distance=max(30, h * 1.6))

    def _update_estimates(self):
        w = self.rocket.validate(); self.warn.setText("<span style='color:#fbbf24'>" + "<br>".join(w) + "</span>" if w else "<span style='color:#34d399'>Design OK</span>")
        if not self.rocket.cores: self.est_table.setRowCount(0); return
        e = self.rocket.estimates()
        rows = [("Total launch mass", f"{e['launch_mass_kg']:,.0f} kg"), ("Mass ratio (m0/mf)", f"{e['mass_ratio']:.2f}"), ("Thrust-to-weight (sea level, Earth)", f"{e['twr_sl']:.2f}"),
                ("Delta-v (Tsiolkovsky, vacuum Isp)", f"{e['delta_v_mps']:,.0f} m/s"), ("Total burn duration", f"{e['burn_time_s']:,.0f} s"),
                ("Max acceleration (vacuum, no drag)", f"{e['max_accel_ms2']:.1f} m/s^2 ({e['max_accel_ms2'] / 9.80665:.1f} g)"),
                ("Height / diameter", f"{e['height_m']:.1f} m / {e['diameter_m']:.2f} m"), ("Center of mass (from base)", f"{e['com_m']:.2f} m"),
                ("Center of pressure (Barrowman est.)", f"{e['cop_m']:.2f} m"), ("Static margin", f"{e['static_margin_cal']:.2f} cal ({'stable' if e['static_margin_cal'] > 0 else 'UNSTABLE: needs active control'})"),
                ("Moment of inertia (transverse)", f"{e['inertia_transverse_kgm2']:.3e} kg m^2"), ("Moment of inertia (axial)", f"{e['inertia_axial_kgm2']:.3e} kg m^2")]
        for st in e["stages"]: rows.append((f"  dv {st['stage']}", f"{st['dv']:,.0f} m/s in {st['burn_s']:.0f} s"))
        self.est_table.setRowCount(len(rows))
        for i, (a, b) in enumerate(rows): self.est_table.setItem(i, 0, QTableWidgetItem(a)); self.est_table.setItem(i, 1, QTableWidgetItem(b))
        self.est_table.resizeColumnToContents(0)

    # ---------------- actions ----------------
    def add_stage(self, kind):
        n = len(self.rocket.stages) + 1
        s = Stage(f"{'Booster' if kind == 'booster' else 'Stage'} {n}", kind, 1.5 if kind == "booster" else 3.0, 20, 3000, 30000, 0, Engine(1, 400e3, 330, 290))
        if kind == "booster": s.booster_count = 2; s.length_m = 25
        self.rocket.stages.append(s); self._refresh_list(); self.list.setCurrentRow(len(self.rocket.stages) - 1); self._changed()

    def duplicate(self):
        s = self._cur()
        if s: c = copy.deepcopy(s); c.name += " copy"; self.rocket.stages.append(c); self._changed(True)

    def remove(self):
        r = self.list.currentRow()
        if len(self.rocket.stages) > 1 and r >= 0: del self.rocket.stages[r]; self._changed(True)

    def move(self, d):
        r = self.list.currentRow(); n = r + d
        if 0 <= n < len(self.rocket.stages): st = self.rocket.stages; st[r], st[n] = st[n], st[r]; self._changed(True); self.list.setCurrentRow(n)

    def set_rocket(self, rocket):
        self.rocket = copy.deepcopy(rocket); self._loading = True; self.name_edit.setText(rocket.name)
        self.w_payload.setValue(rocket.payload_mass_kg); self.w_cd.setValue(rocket.cd); self.nose_shape.setCurrentText(rocket.nose.shape)
        self.nose_len.setValue(rocket.nose.length_m); self.nose_mass.setValue(rocket.nose.mass_kg); self._loading = False
        self._refresh_list(); self.list.setCurrentRow(0); self._changed()

    def save(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save rocket design", f"{self.rocket.name}.rocket.json", "AstraX rocket (*.json)")
        if p: self.rocket.save(p)

    def load(self):
        p, _ = QFileDialog.getOpenFileName(self, "Load rocket design", "", "AstraX rocket (*.json)")
        if p:
            try: self.set_rocket(Rocket.load(p))
            except Exception as ex: QMessageBox.warning(self, "Load failed", str(ex))

    def import_obj(self):
        p, _ = QFileDialog.getOpenFileName(self, "Import OBJ model", "", "Wavefront OBJ (*.obj)")
        if p:
            try: load_obj(p); self.rocket.custom_mesh_path = p; self._changed()
            except Exception as ex: QMessageBox.warning(self, "Import failed", str(ex))

    def export_obj(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export OBJ", "rocket.obj", "Wavefront OBJ (*.obj)")
        if p: export_obj(build_rocket_parts(self.rocket), p)
