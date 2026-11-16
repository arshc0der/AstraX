"""AstraX main window: viewport + explorer + inspector + telemetry dock + toolbar. Wiring only; physics is in astrax/."""
import os, copy, logging, datetime
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QDesktopServices
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import (QScrollArea, QFrame, QMainWindow, QDockWidget, QTabWidget, QToolBar, QComboBox, QLabel, QWidget, QVBoxLayout, QGridLayout, QDoubleSpinBox, QTreeWidget,
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

log = logging.getLogger("astrax")
SPEEDS = ["0.1x", "0.5x", "1x", "2x", "5x", "10x", "50x", "100x", "1000x", "Custom..."]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f"AstraX {__version__} - Spaceflight Simulation Laboratory"); self.resize(1500, 900); self.setMinimumSize(900, 600); self.setStyleSheet(STYLE)
        self.log_path = setup_logging(); self.settings = QSettings("AstraX", "AstraX2")
        self.system = SolarSystem(); self.rocket = default_rocket(); self.cfg = SimConfig(method="rk4", dt_mode="auto")
        L, plan = earth_leo(); self.launch, self.plan = L, plan; self.worker = None; self.runtime = None; self.sim = None; self.rec = None
        self._frames = 0; self._fps = 0.0; self._fps_t = 0.0; self._last_events = 0

        # central workspaces
        self.tabs = QTabWidget(); self.setCentralWidget(self.tabs)
        self.viewport = SpaceViewport(); box = QWidget(); g = QGridLayout(box); g.setContentsMargins(0, 0, 0, 0); g.addWidget(self.viewport, 0, 0)
        self.overlay = QLabel(""); self.overlay.setObjectName("mono"); self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents); self.overlay.setStyleSheet("background: rgba(10,14,19,160); padding: 6px; border-radius: 4px;")
        g.addWidget(self.overlay, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.designer = RocketDesigner(self.rocket); self.education = EducationPanel(lambda: self.rocket, lambda: self.system)
        self.tabs.addTab(box, make_icon("planet"), "Simulation"); self.tabs.addTab(self._scroll(self.designer), make_icon("rocket"), "Rocket designer"); self.tabs.addTab(self._scroll(self.education), "Learn")
        self.designer.rocket_changed.connect(self._rocket_edited); self.designer.use_in_simulation.connect(self._use_rocket)

        # docks
        self.explorer = QTreeWidget(); self.explorer.setHeaderHidden(True); self.explorer.itemDoubleClicked.connect(self._explorer_focus)
        self._dock("Explorer", self.explorer, Qt.DockWidgetArea.LeftDockWidgetArea)
        self.planets = PlanetInspector(self.system); self.planets.changed.connect(self._planet_changed); self.planets.selected.connect(self._planet_selected)
        self.mission = MissionPanel([b.name for b in self.system.bodies]); self.mission.scenario_applied.connect(self._scenario_applied); self.mission.script_requested.connect(self._script)
        self.rtabs = QTabWidget(); self.rtabs.addTab(self._scroll(self.mission), "Mission control"); self.rtabs.addTab(self._scroll(self.planets), "Planet inspector")
        self.d_right = self._dock("Properties & Mission", self.rtabs, Qt.DockWidgetArea.RightDockWidgetArea); self.d_right.setMinimumWidth(320)
        self.telemetry = TelemetryPanel(); self.d_tel = self._dock("Telemetry & timeline", self._scroll(self.telemetry), Qt.DockWidgetArea.BottomDockWidgetArea); self.d_tel.setMinimumHeight(150)
        self.console = QTextEdit(); self.console.setReadOnly(True); self.d_con = self._dock("Event log", self.console, Qt.DockWidgetArea.BottomDockWidgetArea); self.tabifyDockWidget(self.d_tel, self.d_con); self.d_tel.raise_()

        self._build_toolbar(); self._build_menus(); self._build_statusbar()
        self.viewport.init_bodies(self.system); self.viewport.refresh_orbits(); self.viewport.set_rocket(self.rocket)
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
        self.cam = QComboBox(); self.cam.addItems(["Orbit", "Free", "Follow rocket", "Follow selected body", "First person (rocket)"]); self.cam.currentIndexChanged.connect(self._camera_mode); tb.addWidget(self.cam)
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
        t = self.menuBar().addMenu("&Tools"); t.addAction(self._act("Open logs folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(os.path.dirname(self.log_path))))))
        h = self.menuBar().addMenu("&Help"); h.addAction(self._act("About AstraX", lambda: QMessageBox.about(self, "AstraX", f"AstraX {__version__}\nOpen-source (MIT) spaceflight simulation laboratory.\nResults are NOT validated mission predictions.")))

    def _build_statusbar(self):
        sb = self.statusBar(); self.l_time = QLabel(); self.l_met = QLabel(); self.l_acc = QLabel(); self.l_dt = QLabel(); self.l_perf = QLabel(); self.l_fps = QLabel(); self.l_warn = QLabel()
        for l in (self.l_time, self.l_met, self.l_acc, self.l_dt, self.l_perf, self.l_fps): sb.addWidget(l)
        sb.addPermanentWidget(self.l_warn)

    # ---------------- simulation lifecycle ----------------
    def rebuild_simulation(self):
        if self.worker: self.worker.quit_thread(); self.worker.wait(2000)
        self.sim = Simulation(self.system, self.rocket, self.launch, self.plan, self.cfg); self.runtime = MissionRuntime(self.sim, self._log)
        self.rec = Recorder(self.cfg.record_interval_s); self.rec.maybe_record(self.sim, True)
        self.worker = SimWorker(self.sim, self.rec, self.runtime); self.worker.snapshot.connect(self.on_snapshot); self.worker.finished_run.connect(self._run_finished)
        self.telemetry.set_recorder(self.rec, self.launch.target_body); self.viewport.clear_trail(); self.viewport.refresh_orbits()
        self.viewport.focus = "Rocket" if self.launch.start_mode == "pad" else "Earth"; self._speed_changed(self.speed.currentText()); self.worker.start()
        self._last_events = 0; self.a_play.setText("Run"); self.a_play.setIcon(make_icon("play")); log.info("Simulation rebuilt: %s", self.rocket.name)

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
    def _rocket_edited(self, rocket): self.viewport.set_rocket(rocket); self.rocket = rocket
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
        self.viewport.update_scene(s); self.telemetry.update_live(s); tm = s["tm"]
        self.overlay.setText(f"{tm['status']}   T+{tm['met_s']:,.0f}s   {tm['body']}  alt {tm['altitude_m'] / 1e3:,.1f} km   v {tm['speed_mps']:,.0f} m/s   {self.viewport.overlay_text}" if self.viewport.layers["Info overlay"] else "")
        self.l_time.setText(f"  Sim time: {datetime.timedelta(seconds=int(s['t']))}  "); self.l_met.setText(f"MET: {tm['met_s']:,.1f}s  ")
        self.l_acc.setText(f"Accel: requested {s['accel']:g}x / achieved {s['achieved']:.3g}x  "); self.l_dt.setText(f"dt: {s['dt']:.4g}s ({self.cfg.method})  "); self.l_perf.setText(f"Physics: {s['sps']:,.0f} steps/s  ")
        self._frames += 1; import time; now = time.perf_counter()
        if now - self._fps_t > 1.0: self._fps = self._frames / (now - self._fps_t); self._frames = 0; self._fps_t = now
        self.l_fps.setText(f"FPS: {self._fps:.0f}  ")
        slow = (not s["paused"]) and s["achieved"] < 0.9 * s["accel"]
        w = list(s["warnings"]) + (["Playback limited by CPU: physics NOT coarsened - running slower than requested."] if slow else [])
        self.l_warn.setText(f"<span style='color:#fbbf24'>{w[0]}</span>" if w else "<span style='color:#34d399'>numerics OK</span>")
        for t, m in self.sim.events[self._last_events:]: self._log(f"T+{t:,.1f}s  {m}")
        self._last_events = len(self.sim.events)

    # ---------------- camera / explorer ----------------
    def _camera_mode(self, i):
        self.viewport.set_mode(["orbit", "free", "follow_rocket", "follow_body", "first_person"][i])
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

    def _reset_layout(self): self.settings.remove("layout"); QMessageBox.information(self, "Layout", "Layout will reset on next start.")
    def closeEvent(self, e):
        self.settings.setValue("layout", self.saveState())
        if self.worker: self.worker.quit_thread(); self.worker.wait(2000)
        super().closeEvent(e)
