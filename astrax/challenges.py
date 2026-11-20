"""Educational challenges: a scenario + a pass/fail rule. Run headless; the UI loads them as scenarios."""
from __future__ import annotations
import copy
from dataclasses import dataclass
from .simulation import Simulation, SimConfig, LaunchConfig, Phase
from .missions import earth_leo, moon_descent
from .rocket import default_rocket
from .rocket_library import lunar_lander


@dataclass
class ChallengeResult:
    name: str; passed: bool; score: float; message: str; sim: object = None


def _fly(sim, until_phase=None, max_met=2400.0):
    last = len(sim.plan) - 1 if until_phase is None else until_phase
    while sim.met < max_met and not sim.terminal() and sim.phase_idx < last: sim.step()
    return sim


def first_orbit(rocket=None):
    L, plan = earth_leo(200e3, 6.0); sim = _fly(Simulation(rocket=rocket or default_rocket(), launch=L, plan=plan, config=SimConfig(dt_mode="auto"))); tm = sim.telemetry()
    ok = sim.status == "FLYING" and tm["periapsis_alt_m"] >= 150e3 and tm["ecc"] < 0.05
    return ChallengeResult("First orbit", ok, tm["periapsis_alt_m"] / 1e3, f"Orbit {tm['periapsis_alt_m'] / 1e3:.0f} x {tm['apoapsis_alt_m'] / 1e3:.0f} km, status {sim.status}.", sim)


def gentle_ascent(rocket=None, q_limit_kpa=30.0):
    L, plan = earth_leo(200e3, 6.0); r = copy.deepcopy(rocket or default_rocket()); r.limits.max_q_pa = q_limit_kpa * 1e3 / 1.0
    sim = _fly(Simulation(rocket=r, launch=L, plan=plan, config=SimConfig(dt_mode="auto"))); tm = sim.telemetry(); q = sim.peak["q"] / 1e3
    ok = sim.status == "FLYING" and tm["periapsis_alt_m"] >= 150e3 and q <= q_limit_kpa
    return ChallengeResult("Gentle ascent", ok, -q, f"Reached orbit with max-Q {q:.1f} kPa (limit {q_limit_kpa:g} kPa)." if ok else f"Max-Q {q:.1f} kPa, status {sim.status}, periapsis {tm['periapsis_alt_m'] / 1e3:.0f} km.", sim)


def moon_landing(rocket=None):
    L, plan = moon_descent(8000.0); sim = Simulation(rocket=rocket or lunar_lander(), launch=L, plan=plan, config=SimConfig(dt_mode="auto"))
    while sim.met < 900 and not sim.terminal(): sim.step()
    tm = sim.telemetry(); ok = sim.status == "LANDED"
    return ChallengeResult("Moon soft landing", ok, tm["propellant_kg"], f"{sim.status}; propellant left {tm['propellant_kg']:,.0f} kg.", sim)


def abort_at_max_q(rocket=None):
    L, plan = earth_leo(200e3, 6.0); sim = Simulation(rocket=rocket or default_rocket(), launch=L, plan=plan, config=SimConfig(dt_mode="auto")); peak = 0.0
    while sim.met < 400 and not sim.terminal():
        sim.step(); q = sim._q_now()
        if q > 20e3 and q < peak * 0.98: break
        peak = max(peak, q)
    sim.abort()
    while not sim.terminal() and sim.met < 3000: sim.step()
    ok = sim.status == "LANDED" and sim.capsule
    return ChallengeResult("Abort at max-Q", ok, sim.met, f"Aborted near max-Q ({peak / 1e3:.0f} kPa); capsule {sim.status}.", sim)


CHALLENGES = {
    "First orbit": (first_orbit, "Reach a stable circular 200 km orbit with the demo rocket."),
    "Gentle ascent": (gentle_ascent, "Reach orbit keeping max-Q under 30 kPa."),
    "Moon soft landing": (moon_landing, "Land the lunar lander from 8 km at under 10 m/s."),
    "Abort at max-Q": (abort_at_max_q, "Trigger an abort at max-Q and recover the payload capsule."),
}
