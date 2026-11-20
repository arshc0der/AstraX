"""Telemetry recording, run logging, CSV/JSON session export and mission reports (no Qt)."""
from __future__ import annotations
import csv, json, logging, logging.handlers, os, time, datetime, threading
import numpy as np
from . import __version__

NUMERIC = ["t_s", "met_s", "altitude_m", "speed_mps", "surface_speed_mps", "mass_kg", "propellant_kg", "thrust_n",
           "throttle", "accel_thrust_ms2", "g_load", "dynamic_pressure_pa", "kinetic_j", "potential_j",
           "total_energy_j", "specific_energy_jkg", "sma_m", "ecc", "inc_deg", "apoapsis_alt_m", "periapsis_alt_m",
           "period_s", "dist_target_m", "dv_spent_mps", "gravity_force_dominant_n", "rp_x", "rp_y", "rp_z",
           "rel_x", "rel_y", "rel_z", "dist_sun_m", "mach", "aoa_deg", "heat_flux_w_m2", "stress_mpa", "drag_n", "axial_g"]
UNITS = {"t_s": "s", "met_s": "s", "altitude_m": "m", "speed_mps": "m/s", "surface_speed_mps": "m/s", "mass_kg": "kg",
         "propellant_kg": "kg", "thrust_n": "N", "throttle": "-", "accel_thrust_ms2": "m/s^2", "g_load": "g",
         "dynamic_pressure_pa": "Pa", "kinetic_j": "J", "potential_j": "J", "total_energy_j": "J",
         "specific_energy_jkg": "J/kg", "sma_m": "m", "ecc": "-", "inc_deg": "deg", "apoapsis_alt_m": "m",
         "periapsis_alt_m": "m", "period_s": "s", "dist_target_m": "m", "dv_spent_mps": "m/s",
         "gravity_force_dominant_n": "N", "rp_x": "m", "rp_y": "m", "rp_z": "m", "rel_x": "m", "rel_y": "m",
         "rel_z": "m", "dist_sun_m": "m", "mach": "-", "aoa_deg": "deg", "heat_flux_w_m2": "W/m^2", "stress_mpa": "MPa", "drag_n": "N", "axial_g": "g"}


def setup_logging(log_dir="logs", level=logging.INFO) -> str:
    """Create a rotating run-log file `logs/astrax_YYYYmmdd_HHMMSS.log`; returns its path."""
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(log_dir, f"astrax_{datetime.datetime.now():%Y%m%d_%H%M%S}.log")
    lg = logging.getLogger("astrax"); lg.setLevel(level)
    for h in list(lg.handlers): lg.removeHandler(h)
    fh = logging.handlers.RotatingFileHandler(path, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")); lg.addHandler(fh)
    lg.info("AstraX %s log started", __version__)
    return path


class Recorder:
    """Samples Simulation.telemetry() at a fixed simulation-time interval."""

    def __init__(self, interval_s=1.0, max_samples=20_000):
        self.interval = interval_s; self.max = max_samples; self.lock = threading.RLock(); self.clear()

    def clear(self):
        with self.lock: self._clear()

    def _clear(self):
        self.data = {k: [] for k in NUMERIC}; self.labels = {"status": [], "stage": [], "body": []}
        self._next = None; self.events: list = []; self.meta: dict = {}

    def maybe_record(self, sim, force=False):
        if self._next is None: self._next = sim.t
        if force or sim.t >= self._next - 1e-9:
            tm = sim.telemetry()
            with self.lock:                       # the simulation thread writes, the GUI thread reads
                if len(self.data["t_s"]) >= self.max:      # keep memory bounded: drop every 2nd sample, halve the rate
                    for k in self.data: self.data[k] = self.data[k][::2]
                    for k in self.labels: self.labels[k] = self.labels[k][::2]
                    self.interval *= 2
                for k in NUMERIC: self.data[k].append(float(tm[k]))
                for k in self.labels: self.labels[k].append(str(tm[k]))
            self._next = sim.t + self.interval
            return True
        return False

    def arrays(self, *keys):
        """Consistent snapshot: numpy arrays for `keys`, all trimmed to the same length."""
        with self.lock:
            n = min(len(self.data[k]) for k in NUMERIC)
            return [np.asarray(self.data[k][:n], float) for k in keys]

    def array(self, key): return self.arrays(key)[0]
    def __len__(self):
        with self.lock: return min(len(self.data[k]) for k in NUMERIC)

    # ---- export ----
    def export_csv(self, path):
        with self.lock, open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([f"{k} [{UNITS[k]}]" for k in NUMERIC] + ["status", "stage", "body"])
            for i in range(len(self.data["t_s"])):
                w.writerow([self.data[k][i] for k in NUMERIC] + [self.labels["status"][i], self.labels["stage"][i], self.labels["body"][i]])

    def to_dict(self):
        return {"astrax_format": "session/1", "version": __version__, "saved": datetime.datetime.now().isoformat(),
                "meta": self.meta, "events": self.events, "units": UNITS, "data": self.data, "labels": self.labels}

    def save_session(self, path):
        with open(path, "w", encoding="utf-8") as f: json.dump(self.to_dict(), f)

    @staticmethod
    def load_session(path) -> "Recorder":
        with open(path, encoding="utf-8") as f: d = json.load(f)
        r = Recorder(); n = len(d["data"]["t_s"]); r.data = {k: d["data"].get(k, [0.0] * n) for k in NUMERIC}; r.labels = d["labels"]; r.events = d.get("events", []); r.meta = d.get("meta", {})
        return r


def mission_report_markdown(sim, rec: Recorder, estimates: dict | None = None, notes="") -> str:
    """Markdown report. ESTIMATES and SIMULATION RESULTS are kept in separate, labelled sections."""
    tm = sim.telemetry(); n = len(rec)
    def mx(k): return float(np.max(rec.array(k))) if n else float("nan")
    L = [f"# AstraX Mission Report", f"Generated {datetime.datetime.now():%Y-%m-%d %H:%M:%S} - AstraX {__version__}", "",
         f"**Rocket:** {sim.rocket.name}  \n**Launch body:** {sim.launch.body}  \n**Integrator:** {sim.cfg.method}, "
         f"dt mode {sim.cfg.dt_mode} ({sim.cfg.dt_s} s)  \n**Final status:** {tm['status']}", "",
         "## Pre-flight ESTIMATES (analytic, not simulated)"]
    if estimates:
        for k in ("launch_mass_kg", "mass_ratio", "twr_sl", "delta_v_mps", "burn_time_s", "max_accel_ms2", "static_margin_cal"):
            if k in estimates: L.append(f"- {k}: {estimates[k]:.4g}")
    L += ["", "## SIMULATION RESULTS", f"- Samples recorded: {n}", f"- Mission elapsed time: {tm['met_s']:.1f} s",
          f"- Max altitude: {mx('altitude_m') / 1e3:.2f} km", f"- Max speed (vs dominant body): {mx('speed_mps'):.1f} m/s",
          f"- Max thrust acceleration: {mx('accel_thrust_ms2'):.2f} m/s^2 ({mx('g_load'):.2f} g)",
          f"- Max dynamic pressure (Max-Q): {sim.max_q / 1e3:.2f} kPa", f"- Delta-v spent (from mass change): {tm['dv_spent_mps']:.1f} m/s",
          f"- Propellant remaining: {tm['propellant_kg']:,.0f} kg", f"- Final orbit about {tm['body']}: "
          f"periapsis {tm['periapsis_alt_m'] / 1e3:.1f} km, apoapsis {tm['apoapsis_alt_m'] / 1e3:.1f} km, e = {tm['ecc']:.5f}",
          "", "## Event log"] + [f"- T+{t:,.1f} s: {m}" for t, m in sim.events]
    L += ["", "## Assumptions & limitations",
          "- Point-mass N-body gravity; mean Keplerian initial elements (not a JPL ephemeris).",
          "- Simplified atmosphere/drag (no lift, no winds, constant Cd). Guidance is zero-order hold per step.",
          "- Results are NOT validated mission predictions. See docs/PHYSICS.md for the validation status."]
    if notes: L += ["", "## Notes", notes]
    return "\n".join(L)


def save_report(path, sim, rec, estimates=None, notes="", make_plots=True):
    """Write report .md; if matplotlib is installed also write PNG graphs next to it."""
    base = os.path.splitext(path)[0]; md = mission_report_markdown(sim, rec, estimates, notes)
    if make_plots and len(rec):
        try:
            import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
            fig, ax = plt.subplots(2, 2, figsize=(11, 7)); t = rec.array("met_s")
            ax[0, 0].plot(t, rec.array("altitude_m") / 1e3); ax[0, 0].set(title="Altitude", xlabel="MET [s]", ylabel="Altitude [km]")
            ax[0, 1].plot(t, rec.array("speed_mps")); ax[0, 1].set(title="Speed (vs dominant body)", xlabel="MET [s]", ylabel="Speed [m/s]")
            ax[1, 0].plot(t, rec.array("propellant_kg")); ax[1, 0].set(title="Propellant", xlabel="MET [s]", ylabel="Mass [kg]")
            ax[1, 1].plot(t, rec.array("total_energy_j") / 1e12); ax[1, 1].set(title="Orbital total energy", xlabel="MET [s]", ylabel="Energy [TJ]")
            for a in ax.ravel(): a.grid(alpha=.3)
            fig.tight_layout(); fig.savefig(base + "_graphs.png", dpi=130); plt.close(fig)
            md += f"\n\n![graphs]({os.path.basename(base)}_graphs.png)\n"
        except Exception:
            pass
    with open(path, "w", encoding="utf-8") as f: f.write(md)
    return path
