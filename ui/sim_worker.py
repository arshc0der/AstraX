"""Background simulation thread: physics never runs on the GUI thread, so the UI stays responsive."""
import time, threading, logging, queue
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

log = logging.getLogger("astrax")


class SimWorker(QThread):
    snapshot = pyqtSignal(object)      # dict with telemetry + arrays for rendering (copies, thread-safe)
    finished_run = pyqtSignal(str)
    prediction = pyqtSignal(object)    # (points_km_relative_to_body, body_name) or None
    preview = pyqtSignal(object)       # maneuver_preview() dict

    def __init__(self, sim, recorder, runtime=None):
        super().__init__()
        self.sim, self.rec, self.runtime = sim, recorder, runtime
        self.lock = threading.Lock(); self.paused = True; self.accel = 1.0; self._quit = False
        self.max_substeps_wall = 0.025         # wall-clock seconds of physics per frame (keeps UI fluid)
        self.achieved = 1.0; self.sps = 0.0; self._reset_req = False; self._stage_req = False
        self._last_emit = 0.0; self._warn_t = 0.0; self.warnings = []; self._cmds = queue.Queue()

    # ---- thread-safe commands ----
    def set_paused(self, v):
        with self.lock: self.paused = v
    def set_accel(self, a):
        with self.lock: self.accel = max(1e-3, float(a))
    def request_reset(self): self._reset_req = True
    def request_stage(self): self._stage_req = True
    def command(self, name, *args): self._cmds.put((name, args))      # run on the simulation thread (no data races)

    def _handle(self, name, args):
        s = self.sim
        if name == "emergency": s.emergency(*args)
        elif name == "impulse": s.apply_impulse(*args)
        elif name == "predict":
            pts, body = s.predict(*args); self.prediction.emit((pts / 1000.0, body))
        elif name == "preview": self.preview.emit(s.maneuver_preview(*args))
        elif name == "clear_prediction": self.prediction.emit(None)
    def quit_thread(self): self._quit = True

    def _hook(self, sim):
        if self.runtime is not None and self.runtime.is_active: self.runtime.execute_step()
        self.rec.maybe_record(sim)

    def _emit(self, force=False):
        now = time.perf_counter()
        if not force and now - self._last_emit < 1 / 30: return
        self._last_emit = now; s = self.sim
        alive = [d for d in s.debris if d["alive"]]
        snap = dict(status=s.status, throttle=s.throttle, capsule=s.capsule, explosion=s.explosion, orbit_log=list(s.orbit_log),
                    debris_pos=(np.array([d["pos"] for d in alive]) if alive else np.zeros((0, 3))), debris_kind=[d["kind"] for d in alive],
                    tm=s.telemetry(), bp=s.bp.copy(), rp=s.rp.copy(), rv=s.rv.copy(), direction=s.direction.copy(),
                    names=s.names, achieved=self.achieved, sps=self.sps, accel=self.accel, dt=(s.auto_dt() if s.cfg.dt_mode == "auto" else s.cfg.dt_s),
                    paused=self.paused, warnings=self.warnings, n_jettisoned=len(s.jettisoned), n_events=len(s.events), t=s.t, n_rec=len(self.rec),
                    phase=(s.plan[s.phase_idx].name if 0 <= s.phase_idx < len(s.plan) else "-"))
        self.snapshot.emit(snap)

    def run(self):
        last = time.perf_counter(); self._emit(True)
        while not self._quit:
            if self._reset_req:
                self.sim.reset(); self.rec.clear(); self.rec.maybe_record(self.sim, True); self._reset_req = False; self._emit(True)
                if self.runtime: self.runtime.is_active = False
            if self._stage_req: self.sim.separate_next(); self._stage_req = False
            while not self._cmds.empty():
                try: self._handle(*self._cmds.get_nowait())
                except Exception as ex: log.exception("command failed: %s", ex)
            now = time.perf_counter(); wall = now - last; last = now
            with self.lock: paused, accel = self.paused, self.accel
            if paused or self.sim.terminal():
                if self.sim.terminal() and not paused:
                    self.paused = True; log.info("Run ended: %s", self.sim.status); self.finished_run.emit(self.sim.status)
                if self.sim.status in ("LANDED", "CRASHED"): self.sim._track_surface()
                self._emit(); time.sleep(0.02); continue
            req = min(wall, 0.1) * accel; t0 = time.perf_counter(); s0 = self.sim.steps
            adv, done = self.sim.advance(req, self.max_substeps_wall, self._hook)
            el = max(1e-6, time.perf_counter() - t0); self.sps = (self.sim.steps - s0) / el
            self.achieved = adv / max(1e-9, min(wall, 0.1))      # achieved time acceleration (may fall below requested)
            if time.perf_counter() - self._warn_t > 1.0:
                self.warnings = self.sim.stability_warnings(); self._warn_t = time.perf_counter()
                for w in self.warnings: log.warning(w)
            self._emit(); time.sleep(0.001)
        log.info("Simulation thread stopped")
