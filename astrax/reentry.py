"""Planar ballistic atmospheric entry: peak deceleration, peak heating, heat load. Validated against Allen-Eggers (1953).

State is integrated in the orbital plane (x horizontal at entry, y radial) with gravity, drag and Sutton-Graves nose heating. Ballistic
(no lift), non-rotating atmosphere. For a first-look design tool only.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from .constants import G0
from . import atmosphere, aero


@dataclass
class EntryResult:
    peak_decel_g: float; peak_decel_alt_m: float; peak_heat_flux_w_m2: float; peak_heat_alt_m: float; heat_load_j_m2: float
    impact_speed_mps: float; duration_s: float; reached_surface: bool; path: np.ndarray


def entry(body, mass_kg, cd, area_m2, nose_radius_m, speed_mps, gamma_deg, entry_alt_m=None, dt=0.05, max_t=3000.0) -> EntryResult:
    """gamma_deg: flight-path angle below the local horizontal (positive = descending). speed relative to the (non-rotating) atmosphere."""
    top = body.atmosphere.top_altitude_m if body.atmosphere else 100e3; h0 = entry_alt_m or top * 0.999
    R = body.radius_m; mu = body.gm; g = math.radians(gamma_deg)
    pos = np.array([0.0, R + h0]); vel = np.array([speed_mps * math.cos(g), -speed_mps * math.sin(g)])
    t = 0.0; pk_g = pk_h = pk_gh = pk_ha = 0.0; load = 0.0; path = []
    def acc(p, v):
        r = np.linalg.norm(p); a = -mu * p / r ** 3; h = r - R; rho = atmosphere.density(body, h); sp = np.linalg.norm(v)
        D = 0.5 * rho * cd * area_m2 * sp * sp; a_d = -(D / mass_kg) * (v / sp) if sp > 0 else 0 * v
        return a + a_d, D / mass_kg, rho, sp, h
    while t < max_t:
        a1, dg, rho, sp, h = acc(pos, vel)
        if h <= 0: break
        flux = aero.stagnation_heat_flux(body, rho, sp, nose_radius_m); load += flux * dt
        if dg / G0 > pk_g: pk_g, pk_gh = dg / G0, h
        if flux > pk_h: pk_h, pk_ha = flux, h
        k1v = a1; k1x = vel
        a2 = acc(pos + 0.5 * dt * k1x, vel + 0.5 * dt * k1v)[0]; k2x = vel + 0.5 * dt * k1v
        a3 = acc(pos + 0.5 * dt * k2x, vel + 0.5 * dt * a2)[0]; k3x = vel + 0.5 * dt * a2
        a4 = acc(pos + dt * k3x, vel + dt * a3)[0]; k4x = vel + dt * a3
        pos = pos + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x); vel = vel + dt / 6 * (a1 + 2 * a2 + 2 * a3 + a4); t += dt
        if int(t / dt) % 20 == 0: path.append((pos[0], pos[1] - R))
        if sp < 5.0 and h > 0 and t > 10: break
    _, _, _, sp, h = acc(pos, vel)
    return EntryResult(pk_g, pk_gh, pk_h, pk_ha, load, float(sp), t, h <= 0, np.array(path))
