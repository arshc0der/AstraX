"""AstraX main window: viewport + explorer + inspector + telemetry dock + toolbar. Wiring only; physics is in astrax/."""
import os, copy, logging, datetime
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (QApplication, QScrollArea, QFrame, QMainWindow, QDockWidget, QTabWidget, QToolBar, QComboBox, QLabel, QWidget, QVBoxLayout, QGridLayout, QDoubleSpinBox, QTreeWidget,
                             QTreeWidgetItem, QTextEdit, QFileDialog, QMessageBox, QMenu, QInputDialog)
from astrax import __version__, project
from astrax.bodies import SolarSystem
from astrax.rocket import default_rocket
from astrax.simulation import Simulation, SimConfig, LaunchConfig
from astrax.recorder import Recorder, save_report, setup_logging
from astrax.runtime import MissionRuntime
from astrax.missions import earth_leo
from ui.theme import STYLE, make_icon
from ui.viewport import SpaceViewport, LAYERS
from ui.rocket_designer import RocketDesigner
from ui.planet_inspector import PlanetInspector
from ui.mission_panel import MissionPanel
from ui.telemetry import TelemetryPanel
from ui.education import EducationPanel
from ui.sim_worker import SimWorker
from ui.video import ViewportRecorder, screenshot
from ui.emergency_panel import EmergencyPanel
from ui.orbit_panel import OrbitPanel
from ui.survival_dialog import SurvivalDialog
from ui.extra_windows import ViewWindow, GraphWindow
from ui.settings_dialog import SettingsDialog
from ui.planner_panel import PlannerPanel
from ui.studies_panel import StudiesPanel
from ui.challenges_panel import ChallengesPanel
from ui.theme import apply_app_theme, is_dark_theme
from ui.theme import build_style, THEMES

log = logging.getLogger("astrax")
SPEEDS = ["0.1x", "0.5x", "1x", "2x", "5x", "10x", "50x", "100x", "1000x", "Custom..."]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"AstraX {__version__} - Spaceflight Simulation Laboratory"); self.resize(1500, 900); self.setMinimumSize(900, 600)
        _ico = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        if os.path.exists(_ico): from PyQt6.QtGui import QIcon as _QI; self.setWindowIcon(_QI(_ico)); pass
        self.log_path = setup_logging(); self.settings = QSettings("AstraX", "AstraX2"); self.extra = []; self._dialogs = []
        self.prefs = self._load_prefs(); self.setStyleSheet(build_style(self.prefs['theme'], self.prefs['font_pt']))
        self.system = SolarSystem(); self.rocket = default_rocket(); self.cfg = SimConfig(method="rk4", dt_mode="auto")
        L, plan = earth_leo(); self.launch, self.plan = L, plan; self.worker = None; self.runtime = None; self.sim = None; self.rec = None
        self._frames = 0; self._fps = 0.0; self._fps_t = 0.0; self._last_events = 0

        # central workspaces
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self.viewport = SpaceViewport(); box = QWidget(); g = QGridLayout(box); g.setContentsMargins(0, 0, 0, 0); g.addWidget(self.viewport, 0, 0)
        self.overlay = QLabel(""); self.overlay.setObjectName("mono"); self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents); self.overlay.setStyleSheet("background: rgba(10,14,19,160); padding: 6px; border-radius: 4px;")
        g.addWidget(self.overlay, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.banner = QLabel(""); self.banner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents); self.banner.setVisible(False)
        g.addWidget(self.banner, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter); self._banner_timer = QTimer(self); self._banner_timer.setSingleShot(True); self._banner_timer.timeout.connect(lambda: self.banner.setVisible(False))
        self.designer = RocketDesigner(self.rocket); self.education = EducationPanel(lambda: self.rocket, lambda: self.system)
        self.tabs.addTab(box, make_icon("planet"), "Simulation"); self.tabs.addTab(self._scroll(self.designer), make_icon("rocket"), "Rocket designer"); self.tabs.addTab(self._scroll(self.education), "Learn")
        self.designer.rocket_changed.connect(self._rocket_edited); self.designer.use_in_simulation.connect(self._use_rocket); self.designer.survival_requested.connect(self.open_survival)

        # docks
        self.explorer = QTreeWidget(); self.explorer.setHeaderHidden(True); self.explorer.itemDoubleClicked.connect(self._explorer_focus)
        self._dock("Explorer", self.explorer, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.planets = PlanetInspector(self.system); self.planets.changed.connect(self._planet_changed); self.planets.selected.connect(self._planet_selected)
        self.mission = MissionPanel([b.name for b in self.system.bodies]); self.mission.scenario_applied.connect(self._scenario_applied); self.mission.script_requested.connect(self._script); self.mission.preset_loaded.connect(self._preset_loaded)
        self.rtabs = QTabWidget(); self.emergency = EmergencyPanel(lambda: self.worker, lambda: self.cfg); self.orbit = OrbitPanel(lambda: self.worker, lambda: self.rec)
        self.planner = PlannerPanel(lambda: self.system); self.planner.fly_requested.connect(self.fly_transfer)
        self.studies = StudiesPanel(lambda: self.designer.rocket, lambda: self.system); self.challenges = ChallengesPanel(); self.challenges.load_requested.connect(self.load_challenge)
        self.rtabs.addTab(self._scroll(self.mission), "Mission control"); self.rtabs.addTab(self._scroll(self.planets), "Planet inspector")
        self.rtabs.addTab(self._scroll(self.emergency), "Flight safety"); self.rtabs.addTab(self._scroll(self.orbit), "Orbit analysis")
        self.rtabs.addTab(self._scroll(self.planner), "Launch windows"); self.rtabs.addTab(self._scroll(self.studies), "Studies"); self.rtabs.addTab(self._scroll(self.challenges), "Challenges")
        self.d_right = self._dock("Properties & Mission", self.rtabs, Qt.DockWidgetArea.RightDockWidgetArea); self.d_right.setMinimumWidth(320)
        self.telemetry = TelemetryPanel(); self.d_tel = self._dock("Telemetry & timeline", self._scroll(self.telemetry), Qt.DockWidgetArea.BottomDockWidgetArea); self.d_tel.setMinimumHeight(150)
        self.console = QTextEdit(); self.console.setReadOnly(True); self.d_con = self._dock("Event log", self.console, Qt.DockWidgetArea.BottomDockWidgetArea); self.tabifyDockWidget(self.d_tel, self.d_con); self.d_tel.raise_()

        self._build_toolbar(); self._build_menus(); self._build_statusbar()
        self.viewport.init_bodies(self.system); self.viewport.refresh_orbits(); self.viewport.set_rocket(self.rocket)
        self._space_bg(self.prefs["theme"]); self.viewport.trail_len = self.prefs["trail_len"]; self.viewport.body_scale = self.prefs["body_scale"]; self.viewport.show_plume = self.prefs["plume"]
        self.recorder_video = ViewportRecorder(self.viewport)
        self.rebuild_simulation(); self._fill_explorer()
        st = self.settings.value("layout")
        if st: self.restoreState(st)
        self.mission.preset.setCurrentIndex(0)

    # ---------------- helpers ----------------
    @staticmethod
    def _scroll(w):
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.Shape.NoFrame); sa.setWidget(w); sa.setMinimumSize(150, 80); return sa

    def _dock(self, title, widget, area):
        d = QDockWidget(title, self); d.setObjectName(title); d.setWidget(widget); d.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable); self.addDockWidget(area, d); return d

    def _act(self, text, fn, icon=None, shortcut=None, tip="", checkable=False):
        a = QAction(make_icon(icon), text, self) if icon else QAction(text, self); a.setToolTip(f"{tip or text}" + (f"  ({shortcut})" if shortcut else ""))
        if shortcut: a.setShortcut(QKeySequence(shortcut))
        a.setCheckable(checkable); a.triggered.connect(fn); return a

    def _build_toolbar(self):
        tb = QToolBar("Simulation"); tb.setObjectName("sim_toolbar"); self.addToolBar(tb)
        self.a_play = self._act("Run", self.toggle_run, "play", "Space", "Run / pause the simulation"); tb.addAction(self.a_play)
        tb.addAction(self._act("Step", self.single_step, "step", "N", "Advance one physics step while paused"))
        tb.addAction(self._act("Stop", self.stop_run, "stop", None, "Stop (pause and hold final state)"))
        tb.addAction(self._act("Reset", self.reset_run, "reset", "R", "Reset to launch conditions"))
        tb.addAction(self._act("Stage", lambda: self.worker and self.worker.request_stage(), "stage", "S", "Manual stage separation"))
        tb.addSeparator(); tb.addAction(self._act("Slower", lambda: self._bump(-1), "slower", "-", "Decrease time acceleration")); 
        self.speed = QComboBox(); self.speed.addItems(SPEEDS); self.speed.setCurrentText("1x"); self.speed.setToolTip("Time acceleration (simulated seconds per real second)"); self.speed.currentTextChanged.connect(self._speed_changed); tb.addWidget(self.speed)
        tb.addAction(self._act("Faster", lambda: self._bump(1), "faster", "+", "Increase time acceleration"))
        tb.addSeparator(); tb.addWidget(QLabel(" Integrator "))
        self.method = QComboBox(); self.method.addItems(["rk4", "dopri5", "verlet"]); self.method.setToolTip("rk4: fixed-step RK4; dopri5: adaptive Dormand-Prince; verlet: symplectic (best for gravity-only coasts)")
        self.method.setCurrentText(self.cfg.method); self.method.currentTextChanged.connect(self._cfg_changed); tb.addWidget(self.method)
        self.dtmode = QComboBox(); self.dtmode.addItems(["auto", "fixed"]); self.dtmode.setToolTip("auto: timestep chosen from orbit/atmosphere resolution; fixed: your value, with stability warnings"); self.dtmode.currentTextChanged.connect(self._cfg_changed); tb.addWidget(self.dtmode)
        self.dt = QDoubleSpinBox(); self.dt.setRange(0.0005, 3600); self.dt.setDecimals(4); self.dt.setValue(0.05); self.dt.setSuffix(" s"); self.dt.setToolTip("Physics timestep (independent of playback speed)"); self.dt.editingFinished.connect(self._cfg_changed); tb.addWidget(self.dt)
        tb.addSeparator(); tb.addWidget(QLabel(" Camera "))
        self.cam = QComboBox(); self.cam.addItems(["Orbit", "Free", "Follow rocket", "Follow selected body", "First person (rocket)", "Launch camera"]); self.cam.currentIndexChanged.connect(self._camera_mode); tb.addWidget(self.cam)
        for txt, v in (("Top", "top"), ("Side", "side"), ("Front", "front"), ("Iso", "iso")): tb.addAction(self._act(txt, lambda _=False, v=v: self.viewport.set_view(v), None, None, f"{txt} view"))
        tb.addAction(self._act("Reset cam", self.viewport.reset_camera, None, "Home", "Reset camera")); tb.addAction(self._act("Focus", self._focus_selected, None, "F", "Focus on selected object"))
        tb.addSeparator(); self.a_rec = self._act("Record", self.toggle_record, "record", None, "Record the viewport to GIF/MP4", True); tb.addAction(self.a_rec); tb.addAction(self._act("Snapshot", self.take_snapshot, "camera", None, "Save a PNG of the viewport"))

    def _build_menus(self):
        m = self.menuBar().addMenu("&File")
        for t, f in (("New default scenario", self.new_scenario), ("Open scenario...", self.open_scenario), ("Save scenario...", self.save_scenario), (None, None), ("Export telemetry CSV...", lambda: self.telemetry.export_csv()),
                     ("Export mission report...", self.export_report), ("Save session...", lambda: self.telemetry.save_session()), ("Load session...", lambda: self.telemetry.load_session()), (None, None), ("Exit", self.close)):
            m.addAction(self._act(t, f)) if t else m.addSeparator()
        v = self.menuBar().addMenu("&View"); lm = v.addMenu("Visualisation layers")
        for name in LAYERS:
            a = self._act(name, lambda c, n=name: self.viewport.set_layer(n, c), checkable=True); a.setChecked(self.viewport.layers[name]); lm.addAction(a)
        v.addAction(self._act("Body size exaggeration...", self._body_scale)); v.addAction(self._act("Reset window layout", self._reset_layout))
        for d in (self.d_right, self.d_tel, self.d_con): v.addAction(d.toggleViewAction())
        wm = self.menuBar().addMenu("&Window"); wm.addAction(self._act("New 3D view window", self.new_view)); wm.addAction(self._act("New graph window", self.new_graph)); wm.addAction(self._act("Close all extra windows", self.close_extra))
        t = self.menuBar().addMenu("&Tools"); t.addAction(self._act("Design survival test...", self.open_survival)); t.addAction(self._act("Settings & customisation...", self.open_settings)); t.addSeparator(); t.addAction(self._act("Open logs folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(os.path.dirname(self.log_path))))))
        h = self.menuBar().addMenu("&Help"); h.addAction(self._act("About AstraX", self.show_about))

    def _build_statusbar(self):
        sb = self.statusBar(); self.l_time = QLabel(); self.l_met = QLabel(); self.l_acc = QLabel(); self.l_dt = QLabel(); self.l_perf = QLabel(); self.l_fps = QLabel(); self.l_warn = QLabel()
        for l in (self.l_time, self.l_met, self.l_acc, self.l_dt, self.l_perf, self.l_fps): sb.addWidget(l)
        sb.addPermanentWidget(self.l_warn)

    # ---------------- simulation lifecycle ----------------
    def rebuild_simulation(self):
        if self.worker: self.worker.quit_thread(); self.worker.wait(2000)
        self.sim = Simulation(self.system, self.rocket, self.launch, self.plan, self.cfg); self.runtime = MissionRuntime(self.sim, self._log)
        self.cfg.record_interval_s = self.prefs["record_interval_s"]; self.rec = Recorder(self.cfg.record_interval_s); self.rec.maybe_record(self.sim, True)
        self.worker = SimWorker(self.sim, self.rec, self.runtime); self.worker.snapshot.connect(self.on_snapshot); self.worker.finished_run.connect(self._run_finished)
        self.worker.prediction.connect(self.viewport.set_prediction); self.worker.preview.connect(self.orbit.show_preview); self.viewport.set_prediction(None)
        for w in self.extra:
            if isinstance(w, ViewWindow): w.rebuild(self.system, self.rocket)
        self.telemetry.set_recorder(self.rec, self.launch.target_body); self.viewport.clear_trail(); self.viewport.refresh_orbits()
        self.viewport.focus = "Rocket" if self.launch.start_mode == "pad" else "Earth"; self._speed_changed(self.speed.currentText()); self.worker.start()
        self._last_events = 0; self.a_play.setText("Run"); self.a_play.setIcon(make_icon("play")); log.info("Simulation rebuilt: %s", self.rocket.name)

    def show_banner(self, text, color):
        self.banner.setText(text); self.banner.setStyleSheet(f"font-size: 20pt; font-weight: 800; color: {color}; background: rgba(5,8,12,200); padding: 8px 22px; border: 2px solid {color}; border-radius: 8px;"); self.banner.setVisible(True); self._banner_timer.start(4000)

    def _log(self, msg): self.console.append(f"<span style='color:#7e8b9a'>{datetime.datetime.now():%H:%M:%S}</span> {msg}"); log.info(msg)

    def toggle_run(self):
        run = self.worker.paused; self.worker.set_paused(not run)
        self.a_play.setText("Pause" if run else "Run"); self.a_play.setIcon(make_icon("pause" if run else "play"))

    def stop_run(self): self.worker.set_paused(True); self.a_play.setText("Run"); self.a_play.setIcon(make_icon("play"))
    def reset_run(self): self.stop_run(); self.viewport.clear_trail(); self.worker.request_reset(); self._last_events = 0
    def single_step(self):
        if self.worker.paused: self.sim.step(); self.rec.maybe_record(self.sim); self.worker._emit(True)

    def _run_finished(self, status): self._log(f"<b>Run finished: {status}</b>"); self.a_play.setText("Run"); self.a_play.setIcon(make_icon("play"))

    def _speed_changed(self, txt):
        if txt.startswith("Custom"):
            v, ok = QInputDialog.getDouble(self, "Custom time acceleration", "Simulated seconds per real second:", 10.0, 0.001, 1e7, 3)
            if not ok: return
        else: v = float(txt.rstrip("x"))
        if self.worker: self.worker.set_accel(v)

    def _bump(self, d):
        i = max(0, min(len(SPEEDS) - 2, self.speed.currentIndex() + d)); self.speed.setCurrentIndex(i)

    def _cfg_changed(self, *_):
        self.cfg.method = self.method.currentText(); self.cfg.dt_mode = self.dtmode.currentText(); self.cfg.dt_s = self.dt.value()   # shared object: live update
        self.sim.cfg = self.cfg; self.dt.setEnabled(self.cfg.dt_mode == "fixed")

    # ---------------- model edits ----------------
    def _rocket_edited(self, rocket):
        self.viewport.set_rocket(rocket); self.rocket = rocket
        for w in self.extra:
            if isinstance(w, ViewWindow): w.vp.set_rocket(rocket)
    def _use_rocket(self, rocket): self.rocket = rocket; self.viewport.set_rocket(rocket); self.rebuild_simulation(); self.tabs.setCurrentIndex(0); self._fill_explorer()
    def _planet_changed(self, name): self.rebuild_simulation(); self._log(f"Planet data edited: {name} - simulation restarted")
    def _planet_selected(self, name): self.selected_body = name
    def _scenario_applied(self, L, plan): self.launch, self.plan = L, plan; self.rebuild_simulation()

    def _script(self, text, enable):
        if enable:
            ok = self.runtime.compile_script(text); self._log("Script control ON" if ok else "Script failed to compile")
        else: self.runtime.disable(); self._log("Script control OFF")

    # ---------------- snapshots ----------------
    def on_snapshot(self, s):
        self.viewport.update_scene(s); self.telemetry.update_live(s); self.emergency.update_snapshot(s); self.orbit.update_snapshot(s); tm = s["tm"]
        for w in self.extra: w.on_snapshot(s)
        self.overlay.setText(f"{tm['status']}   T+{tm['met_s']:,.0f}s   {tm['body']}  alt {tm['altitude_m'] / 1e3:,.1f} km   v {tm['speed_mps']:,.0f} m/s   {self.viewport.overlay_text}" if self.viewport.layers["Info overlay"] else "")
        self.l_time.setText(f"  Sim time: {datetime.timedelta(seconds=int(s['t']))}  "); self.l_met.setText(f"MET: {tm['met_s']:,.1f}s  ")
        self.l_acc.setText(f"Accel: requested {s['accel']:g}x / achieved {s['achieved']:.3g}x  "); self.l_dt.setText(f"dt: {s['dt']:.4g}s ({self.cfg.method})  "); self.l_perf.setText(f"Physics: {s['sps']:,.0f} steps/s  ")
        self._frames += 1; import time; now = time.perf_counter()
        if now - self._fps_t > 1.0: self._fps = self._frames / (now - self._fps_t); self._frames = 0; self._fps_t = now
        self.l_fps.setText(f"FPS: {self._fps:.0f}  ")
        slow = (not s["paused"]) and s["achieved"] < 0.9 * s["accel"]
        w = list(s["warnings"]) + (["Playback limited by CPU: physics NOT coarsened - running slower than requested."] if slow else [])
        self.l_warn.setText(f"<span style='color:#fbbf24'>{w[0]}</span>" if w else "<span style='color:#34d399'>numerics OK</span>")
        for t, m in self.sim.events[self._last_events:]:
            self._log(f"T+{t:,.1f}s  {m}")
            for key, txt, col in (("VEHICLE LOST", "VEHICLE LOST", "#f87171"), ("LIFTOFF", "LIFTOFF", "#34d399"), ("STAGE SEPARATION", "STAGE SEPARATION", "#2aa9ff"), ("ABORT", "ABORT", "#fbbf24"),
                                  ("PARACHUTE", "PARACHUTE DEPLOYED", "#2aa9ff"), ("LANDED", "TOUCHDOWN", "#34d399"), ("CRASHED", "CRASHED", "#f87171"), ("WARNING", "LOAD WARNING", "#fbbf24")):
                if key in m: self.show_banner(txt + (": " + m.split(": ", 1)[1] if key == "VEHICLE LOST" and ": " in m else ""), col); break
        self._last_events = len(self.sim.events)

    # ---------------- camera / explorer ----------------
    def _camera_mode(self, i):
        self.viewport.set_mode(["orbit", "free", "follow_rocket", "follow_body", "first_person", "launch"][i])
        if i == 3: self._focus_selected()

    def _focus_selected(self): self.viewport.focus_on(getattr(self, "selected_body", "Earth"))
    def _explorer_focus(self, item, col):
        n = item.text(0).split("  ")[0]
        if n in self.sim.names: self.rtabs.setCurrentIndex(1); self.planets.list.setCurrentRow(self.sim.names.index(n)); self.viewport.focus_on(n)
        elif n == "Rocket": self.viewport.focus_on("Rocket")

    def _fill_explorer(self):
        self.explorer.clear(); m = QTreeWidgetItem(["Mission"]); m.addChild(QTreeWidgetItem([f"Launch: {self.launch.body} -> {self.launch.target_body}"]))
        r = QTreeWidgetItem(["Rocket"]); r.addChild(QTreeWidgetItem([self.rocket.name]))
        for s in self.rocket.stages: r.addChild(QTreeWidgetItem([f"{s.name}  ({s.engine.count} engines)"]))
        b = QTreeWidgetItem(["Celestial bodies"])
        for x in self.system.bodies: b.addChild(QTreeWidgetItem([x.name]))
        for it in (m, r, b): self.explorer.addTopLevelItem(it); it.setExpanded(True)

    def _body_scale(self):
        v, ok = QInputDialog.getDouble(self, "Body size exaggeration", "Visual scale of planets (1 = true size):", self.viewport.body_scale, 0.1, 1000, 1)
        if ok: self.viewport.body_scale = v

    # ---------------- files ----------------
    def new_scenario(self): self.system.reset_all(); self.rocket = default_rocket(); self.designer.set_rocket(self.rocket); self.launch, self.plan = earth_leo(); self.mission.set_scenario(self.launch, self.plan); self.planets.set_system(self.system); self.rebuild_simulation(); self._fill_explorer()
    def save_scenario(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save scenario", "scenario.astrax.json", "AstraX scenario (*.json)")
        if p: project.save_scenario(p, self.rocket, self.mission.launch_config(), self.plan, self.cfg, self.system, os.path.basename(p))
    def open_scenario(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open scenario", "", "AstraX scenario (*.json)")
        if not p: return
        try: r, L, plan, c, s, name = project.load_scenario(p)
        except Exception as ex: QMessageBox.warning(self, "Load failed", str(ex)); return
        self.rocket, self.launch, self.plan, self.cfg, self.system = r, L, plan, c, s; self.designer.set_rocket(r); self.mission.set_scenario(L, plan); self.planets.set_system(s)
        self.viewport.init_bodies(s); self.viewport.set_rocket(r); self.rebuild_simulation(); self._fill_explorer()
    def export_report(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export mission report", "mission_report.md", "Markdown (*.md)")
        if p: save_report(p, self.sim, self.rec, self.rocket.estimates()); self._log(f"Report written: {p}")

    def toggle_record(self):
        if self.a_rec.isChecked(): self.recorder_video.start(); self._log("Recording viewport...")
        else:
            p, _ = QFileDialog.getSaveFileName(self, "Save recording", "astrax_recording.gif", "GIF (*.gif);;MP4 (*.mp4)")
            if p:
                try: self.recorder_video.save(p); self._log(f"Recording saved: {p}")
                except Exception as ex: QMessageBox.warning(self, "Recording", str(ex))
            else: self.recorder_video.stop_timer()
    def take_snapshot(self):
        p, _ = QFileDialog.getSaveFileName(self, "Save snapshot", "astrax.png", "PNG (*.png)")
        if p: screenshot(self.viewport, p)

    # ---------------- survival test / extra windows / settings ----------------
    def open_survival(self):
        dlg = SurvivalDialog(self.designer.rocket, self.system, self); dlg.watch_requested.connect(self.watch_launch); self._dialogs = [dlg]; dlg.show()

    def watch_launch(self, rocket, kick):
        from astrax.missions import earth_leo
        self.rocket = copy.deepcopy(rocket); L, plan = earth_leo(200e3, kick); self.launch, self.plan = L, plan
        self.mission.set_scenario(L, plan); self.viewport.set_rocket(self.rocket); self.rebuild_simulation(); self.tabs.setCurrentIndex(0)
        self.cam.setCurrentIndex(5); self.speed.setCurrentText("2x"); self.toggle_run(); self._fill_explorer()

    def new_view(self):
        w = ViewWindow(f"3D view {len(self.extra) + 1}", self.system, self.rocket, self); self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, w); w.setFloating(True); w.show(); self.extra.append(w)

    def new_graph(self):
        w = GraphWindow(f"Graph {len(self.extra) + 1}", lambda: self.rec, "altitude_m", self); self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, w); w.setFloating(True); w.show(); self.extra.append(w)

    def close_extra(self):
        for w in self.extra: w.close(); self.removeDockWidget(w); w.deleteLater()
        self.extra = []

    def _load_prefs(self):
        g = self.settings.value
        return dict(theme=g("theme", "Mission control (dark)"), font_pt=int(g("font_pt", 10)), trail_len=int(g("trail_len", 3000)), body_scale=float(g("body_scale", 1.0)),
                    plume=str(g("plume", "true")).lower() == "true", show_splash=str(g("show_splash", "true")).lower() == "true", record_interval_s=float(g("record_interval_s", 1.0)))

    def open_settings(self):
        dlg = SettingsDialog(self.prefs, self); dlg.applied.connect(self._apply_prefs); self._dialogs = [dlg]; dlg.show()

    def _apply_prefs(self, p):
        self.prefs = p
        for k, v in p.items(): self.settings.setValue(k, v)
        pal = apply_app_theme(QApplication.instance(), p["theme"]); self.setStyleSheet(build_style(p["theme"], p["font_pt"]))
        if getattr(self, "frame_filter", None): self.frame_filter.set_colors(pal)
        self._space_bg(p["theme"])
        for vp in [self.viewport] + [w.vp for w in self.extra if isinstance(w, ViewWindow)]:
            vp.trail_len = p["trail_len"]; vp.body_scale = p["body_scale"]; vp.show_plume = p["plume"]
        self.cfg.record_interval_s = p["record_interval_s"]

    def _space_bg(self, theme):
        """3D background = the theme background on dark themes (space stays dark on the light theme)."""
        from ui.theme import THEMES
        col = THEMES[theme]["BG"] if is_dark_theme(theme) else THEMES["Mission control (dark)"]["BG"]
        self.viewport.set_space_background(col)
        for w in self.extra:
            if isinstance(w, ViewWindow): w.vp.set_space_background(col)

    def show_about(self):
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        d = QDialog(self); d.setWindowTitle("About AstraX"); v = QVBoxLayout(d)
        logo = QLabel(); pm = QPixmap(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo_full.png"))
        if not pm.isNull(): logo.setPixmap(pm.scaledToWidth(560, Qt.TransformationMode.SmoothTransformation)); logo.setAlignment(Qt.AlignmentFlag.AlignCenter); v.addWidget(logo)
        t = QLabel(f"<b>AstraX {__version__}</b><br>Open-source (MIT) spaceflight simulation laboratory.<br>Results are simplified-model results, <b>not</b> validated mission predictions."); t.setAlignment(Qt.AlignmentFlag.AlignCenter); v.addWidget(t)
        b = QPushButton("Close"); b.clicked.connect(d.accept); v.addWidget(b); d.exec()

    # ---------------- presets / transfers / challenges ----------------
    def _preset_loaded(self, name):
        from astrax.missions import PRESET_ROCKETS
        from astrax.rocket_library import get_rocket
        if name in PRESET_ROCKETS:
            self.rocket = get_rocket(PRESET_ROCKETS[name]); self.designer.set_rocket(self.rocket); self.viewport.set_rocket(self.rocket); self._fill_explorer()

    def fly_transfer(self, origin, dest, dep_day, tof_days):
        from astrax import transfer
        from astrax.simulation import Phase
        L, t = transfer.to_launch_config(self.system, origin, dest, dep_day, tof_days); plan = [Phase("Coast to " + dest + " (no mid-course correction)", "coast", 0.0, until={})]
        self.launch, self.plan = L, plan; self.mission.set_scenario(L, plan); self.rebuild_simulation(); self.tabs.setCurrentIndex(0); self.cam.setCurrentIndex(0)
        self.viewport.focus_on("Sun"); self.viewport.setCameraPosition(distance=6e8, elevation=60, azimuth=45); self.worker.set_accel(2e6); self.toggle_run()
        self._log(f"Transfer {origin} -> {dest}: departure v-infinity {t['vinf_dep'] / 1e3:.2f} km/s, time of flight {tof_days:.0f} d; time acceleration set to 2,000,000x")

    def load_challenge(self, name):
        from astrax.rocket import default_rocket
        if name == "Moon soft landing": self.mission.preset.setCurrentText("Moon powered descent (lunar lander)"); self.mission._load_preset()
        else:
            self.rocket = default_rocket(); self.designer.set_rocket(self.rocket)
            if name == "Gentle ascent": self.rocket.limits.max_q_pa = 30e3; self.designer.set_rocket(self.rocket)
            self.mission.preset.setCurrentText("Earth launch to LEO"); self.mission._load_preset()
        self.tabs.setCurrentIndex(0); self._log(f"Challenge loaded: {name}" + (" - press ABORT in Flight safety near max-Q" if name == "Abort at max-Q" else ""))

    def _reset_layout(self): self.settings.remove("layout"); QMessageBox.information(self, "Layout", "Layout will reset on next start.")
    def closeEvent(self, e):
        self.settings.setValue("layout", self.saveState())
        if self.worker: self.worker.quit_thread(); self.worker.wait(2000)
        super().closeEvent(e)
