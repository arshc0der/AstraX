"""Interplanetary launch-window planner: Kepler ephemeris, synodic period, Lambert porkchop grid, transfer -> simulation start.

Heliocentric two-body model with the mean elements in `bodies.py` (Earth uses the Earth-Moon barycentre elements). Not a perturbed
ephemeris: dates are indicative, not for mission design.
"""
from __future__ import annotations
import math
import numpy as np
from .constants import DAY
from .orbital import elements_to_state
from .lambert import lambert
from .simulation import LaunchConfig


def body_state(system, name, t_s):
    """Heliocentric (r, v) of a planet at t_s seconds after J2000 from its Kepler elements."""
    b = system.get(name)
    if b.parent is not None or b.a <= 0: raise ValueError(f"{name} is not a heliocentric body")
    mu = system.bodies[0].gm + b.gm
    M = (b.m0 + math.degrees(math.sqrt(mu / b.a ** 3) * t_s)) % 360.0
    return elements_to_state(b.a, b.e, b.inc, b.raan, b.argp, M, mu)


def synodic_period_days(system, a, b):
    Ta, Tb = system.orbital_period(a), system.orbital_period(b)
    return abs(1.0 / (1.0 / Ta - 1.0 / Tb)) / DAY


def _burn(mu, r_park, vinf):
    return math.sqrt(vinf ** 2 + 2 * mu / r_park) - math.sqrt(mu / r_park)


def transfer_for(system, origin, dest, dep_day, tof_days, park_alt_m=300e3, arrive_alt_m=300e3, prograde=True):
    """Lambert transfer between two planets for a given departure day (after J2000) and time of flight."""
    mu_s = system.bodies[0].gm; t1 = dep_day * DAY; t2 = t1 + tof_days * DAY
    r1, v1b = body_state(system, origin, t1); r2, v2b = body_state(system, dest, t2)
    v1, v2 = lambert(r1, r2, tof_days * DAY, mu_s, prograde)
    vinf_vec = v1 - v1b; vinf_dep = float(np.linalg.norm(vinf_vec)); vinf_arr = float(np.linalg.norm(v2 - v2b))
    bo, bd = system.get(origin), system.get(dest)
    dv_dep = _burn(bo.gm, bo.radius_m + park_alt_m, vinf_dep); dv_arr = _burn(bd.gm, bd.radius_m + arrive_alt_m, vinf_arr)
    return dict(vinf_vec=vinf_vec, vinf_dep=vinf_dep, vinf_arr=vinf_arr, c3=vinf_dep ** 2, dv_dep=dv_dep, dv_arr=dv_arr, dv_total=dv_dep + dv_arr, dep_day=dep_day, tof_days=tof_days)


def porkchop(system, origin="Earth", dest="Mars", dep_start_day=0.0, dep_span_days=800.0, tof_min_days=100.0, tof_max_days=400.0, n_dep=40, n_tof=40,
             park_alt_m=300e3, arrive_alt_m=300e3, progress=None):
    """Grid of transfer costs. Returns dict(dep_days, tof_days, vinf_dep, vinf_arr, dv_total, best) with NaN where no solution."""
    dep = np.linspace(dep_start_day, dep_start_day + dep_span_days, n_dep); tof = np.linspace(tof_min_days, tof_max_days, n_tof)
    vd = np.full((n_dep, n_tof), np.nan); va = vd.copy(); dvt = vd.copy()
    for i, d in enumerate(dep):
        if progress: progress(i, n_dep)
        for j, t in enumerate(tof):
            try:
                r = transfer_for(system, origin, dest, d, t, park_alt_m, arrive_alt_m); vd[i, j], va[i, j], dvt[i, j] = r["vinf_dep"], r["vinf_arr"], r["dv_total"]
            except Exception: pass
    best = None
    if np.isfinite(dvt).any():
        i, j = np.unravel_index(np.nanargmin(dvt), dvt.shape); best = dict(dep_day=float(dep[i]), tof_days=float(tof[j]), vinf_dep=float(vd[i, j]), vinf_arr=float(va[i, j]), dv_total=float(dvt[i, j]), index=(int(i), int(j)))
    return dict(dep_days=dep, tof_days=tof, vinf_dep=vd, vinf_arr=va, dv_total=dvt, best=best, origin=origin, dest=dest)


def to_launch_config(system, origin, dest, dep_day, tof_days, offset_m=5e8):
    """LaunchConfig that starts the rocket on the hyperbolic departure leg (v_infinity preserved) at `offset_m` from the origin body."""
    t = transfer_for(system, origin, dest, dep_day, tof_days)
    return LaunchConfig(body=origin, start_mode="transfer", start_day=dep_day, orbit_altitude_m=offset_m, target_body=dest, extra_velocity_mps=tuple(float(x) for x in t["vinf_vec"])), t
