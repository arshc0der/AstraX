"""Design survival test: fly the rocket through a standard ascent and report whether it survives.

Runs headless (no UI). The standard profile is `missions.earth_leo`; for each trial pitch-kick angle the full ascent is simulated
(Mach-dependent aerodynamics, loads, structural/thermal checks, protective throttling). The best trial is reported, then an
orbit-persistence check coasts a few orbits. A failure may reflect the generic guidance profile rather than the design - the
report says so. This is a SCREENING tool, not certification.
"""
from __future__ import annotations
import math, copy
from dataclasses import dataclass, field
from .bodies import SolarSystem
from .simulation import Simulation, SimConfig
from .missions import earth_leo


@dataclass
class SurvivalResult:
    verdict: str = ""             # SURVIVED | LOST | CRASHED | SUBORBITAL | NO_LIFTOFF | DECAYING | ESCAPED
    headline: str = ""
    reason: str = ""
    kick_deg: float = 0.0
    met_s: float = 0.0
    orbit: dict = field(default_factory=dict)
    peaks: dict = field(default_factory=dict)
    limits: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    trials: list = field(default_factory=list)      # (kick, verdict, headline)
    notes: list = field(default_factory=list)

    @property
    def survived(self): return self.verdict == "SURVIVED"


def _trial(rocket, system, kick, target_alt, cfg, max_met, coast_orbits):
    L, plan = earth_leo(target_alt, kick)
    sim = Simulation(system=copy.deepcopy(system), rocket=rocket, launch=L, plan=plan, config=copy.deepcopy(cfg))
    last = len(plan) - 1
    while sim.met < max_met and not sim.terminal() and sim.phase_idx < last: sim.step()
    tm = sim.telemetry(); r = SurvivalResult(kick_deg=kick, met_s=sim.met, events=list(sim.events), peaks=dict(sim.peak))
    lim = rocket.limits
    r.limits = dict(q=lim.max_q_pa, g=lim.max_axial_g, heat=lim.max_heat_flux_w_m2, fos=lim.factor_of_safety)
    r.orbit = dict(body=tm["body"], peri_km=tm["periapsis_alt_m"] / 1e3, apo_km=tm["apoapsis_alt_m"] / 1e3, ecc=tm["ecc"], inc=tm["inc_deg"])
    if sim.status == "PAD":
        r.verdict, r.headline = "NO_LIFTOFF", "Cannot lift off: sea-level thrust-to-weight is below 1."
    elif sim.status == "DESTROYED":
        r.verdict, r.reason = "LOST", sim.failure_reason; r.headline = f"VEHICLE LOST at T+{sim.destroyed_t - 0:,.0f}s (sim time): {sim.failure_reason}"
        r.headline = f"VEHICLE LOST at T+{sim.met:,.0f} s - {sim.failure_reason}"
    elif sim.status in ("CRASHED", "LANDED"):
        r.verdict, r.headline = "CRASHED", f"Did not reach orbit: vehicle hit the surface at T+{sim.met:,.0f} s."
    else:
        peri = tm["periapsis_alt_m"]
        if tm["ecc"] >= 1.0: r.verdict, r.headline = "ESCAPED", "Reached escape trajectory (hyperbolic) - not a bound orbit."
        elif peri < 100e3: r.verdict, r.headline = "SUBORBITAL", f"Reached space but periapsis is only {peri / 1e3:.0f} km - it will re-enter."
        else:
            T = tm["period_s"]; sim.cfg.failures = True
            sim.plan = []; sim.phase_idx = -1; sim.faults["engine_cutoff"] = True
            sim.advance(coast_orbits * T)
            tm2 = sim.telemetry()
            if sim.status != "FLYING" or tm2["periapsis_alt_m"] < 100e3:
                r.verdict, r.headline = "DECAYING", f"Orbit decays within {coast_orbits} orbits (periapsis {tm2['periapsis_alt_m'] / 1e3:.0f} km)."
            else:
                r.verdict = "SURVIVED"
                r.headline = (f"SURVIVED: stable {tm['periapsis_alt_m'] / 1e3:.0f} x {tm['apoapsis_alt_m'] / 1e3:.0f} km orbit, "
                              f"checked for {coast_orbits} orbits.")
    return r


def run_survival_test(rocket, system=None, target_alt_m=200e3, kicks=(4.0, 6.0, 8.0), coast_orbits=2, protect=True, max_met=2400.0, progress=None) -> SurvivalResult:
    system = system or SolarSystem()
    if rocket.cores and rocket.estimates()["twr_sl"] < 1.0:
        e = rocket.estimates(); r = SurvivalResult(verdict="NO_LIFTOFF", headline=f"Cannot lift off: sea-level thrust-to-weight is {e['twr_sl']:.2f} (needs > 1).")
        r.trials = [(0.0, r.verdict, r.headline)]; r.notes = ["Add engines/thrust or remove mass."]; return r
    cfg = SimConfig(dt_mode="auto", protect=protect, failures=True)
    rank = {"SURVIVED": 6, "DECAYING": 5, "SUBORBITAL": 4, "ESCAPED": 3, "CRASHED": 2, "LOST": 1, "NO_LIFTOFF": 0}
    best = None; trials = []
    for i, k in enumerate(kicks):
        if progress: progress(i, len(kicks), f"Trial {i + 1}/{len(kicks)}: pitch kick {k:g} deg")
        r = _trial(rocket, system, k, target_alt_m, cfg, max_met, coast_orbits); trials.append((k, r.verdict, r.headline))
        if best is None or rank[r.verdict] > rank[best.verdict] or (rank[r.verdict] == rank[best.verdict] and r.met_s > best.met_s and r.verdict == "LOST"): best = r
        if r.verdict in ("SURVIVED", "NO_LIFTOFF"): break
    best.trials = trials
    if best.verdict != "SURVIVED":
        best.notes.append("The standard ascent profile may not suit this vehicle; a failure can reflect guidance (kick angle, throttle) rather than the design itself.")
    best.notes.append("Screening only: simplified aerodynamics, yield-stress check (no buckling/fatigue/thermal soak), Earth ascent to ~200 km.")
    return best
