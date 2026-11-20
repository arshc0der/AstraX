"""Research studies built on the survival test: parameter sweeps, maximum payload, Monte Carlo robustness."""
from __future__ import annotations
import copy, re
import numpy as np
from .rocket import Rocket
from .survival import run_survival_test, SurvivalResult

_TOKEN = re.compile(r"([A-Za-z_]\w*)|\[(\d+)\]")


def _walk(obj, path):
    toks = [(a or int(b)) for a, b in _TOKEN.findall(path)]
    for t in toks[:-1]: obj = obj[t] if isinstance(t, int) else getattr(obj, t)
    return obj, toks[-1]


def get_param(rocket, path):
    o, k = _walk(rocket, path); return o[k] if isinstance(k, int) else getattr(o, k)


def set_param(rocket, path, value):
    o, k = _walk(rocket, path)
    if isinstance(k, int): o[k] = value
    else: setattr(o, k, value)


def _summ(value, r: SurvivalResult):
    return dict(value=float(value), verdict=r.verdict, survived=r.survived, peri_km=r.orbit.get("peri_km", float("nan")), apo_km=r.orbit.get("apo_km", float("nan")),
                max_q_kpa=r.peaks.get("q", 0) / 1e3, max_g=r.peaks.get("g", 0), max_heat_kw=r.peaks.get("heat", 0) / 1e3, stress_ratio=r.peaks.get("stress_ratio", 0), reason=r.reason)


def sweep(rocket: Rocket, path: str, values, system=None, kicks=(6.0,), progress=None):
    """Run the survival test for each value of one parameter (e.g. 'payload_mass_kg', 'stages[0].engine.count', 'cd')."""
    out = []
    for i, v in enumerate(values):
        if progress: progress(i, len(values), f"{path} = {v:g}")
        r = copy.deepcopy(rocket); set_param(r, path, v); out.append(_summ(v, run_survival_test(r, system, kicks=kicks)))
    return out


def max_payload_to_orbit(rocket: Rocket, system=None, hi_kg=None, tol_kg=100.0, kicks=(5.0, 7.0), progress=None):
    """Bisection on payload mass for the largest payload that still reaches (and keeps) a stable orbit with the standard ascent.
    Survival is not strictly monotonic in payload mass; treat the answer as an estimate."""
    lo = 0.0; hi = hi_kg or rocket.payload_mass_kg * 4 + 1000.0; best = None; n = 0
    def ok(m):
        nonlocal n; n += 1; r = copy.deepcopy(rocket); r.payload_mass_kg = m
        if progress: progress(n, 12, f"payload {m:,.0f} kg")
        return run_survival_test(r, system, kicks=kicks).survived
    if not ok(max(lo, 1.0)): return dict(max_payload_kg=0.0, note="Does not reach orbit even with a minimal payload.")
    while hi - lo > tol_kg and n < 14:
        mid = 0.5 * (lo + hi)
        if ok(mid): lo = mid
        else: hi = mid
    return dict(max_payload_kg=lo, note=f"Bisection to {tol_kg:g} kg tolerance ({n} ascents).")


def monte_carlo(rocket: Rocket, n=20, seed=1, system=None, sigma=None, kicks=(6.0,), progress=None):
    """Randomly perturb thrust, Isp, drag, dry mass and fuel load (1-sigma fractions) and report the fraction of successful ascents."""
    sg = dict(thrust=0.03, isp=0.01, cd=0.10, dry_mass=0.03, propellant=0.005); sg.update(sigma or {}); rng = np.random.default_rng(seed); rows = []
    for i in range(n):
        if progress: progress(i, n, f"run {i + 1}/{n}")
        r = copy.deepcopy(rocket); f = lambda k: 1 + rng.normal(0, sg[k])
        r.cd *= max(0.3, f("cd"))
        for s in r.stages:
            s.engine.thrust_vac_n *= f("thrust"); k = f("isp"); s.engine.isp_vac_s *= k; s.engine.isp_sl_s *= k; s.dry_mass_kg *= f("dry_mass"); s.propellant_kg *= f("propellant")
            s.propellant_capacity_kg = max(s.propellant_capacity_kg, s.propellant_kg)
        res = run_survival_test(r, system, kicks=kicks); rows.append(_summ(i, res))
    verdicts = {}
    for r in rows: verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1
    return dict(n=n, success_rate=sum(r["survived"] for r in rows) / max(n, 1), verdicts=verdicts, rows=rows, sigma=sg)
