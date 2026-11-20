"""Aerodynamics, heating and structural-load models (SIMPLIFIED, documented in docs/PHYSICS.md).

* speed of sound a = sqrt(gamma R T); Mach M = v_air / a.   Earth T(h): US Standard Atmosphere 1976 layers.
* Drag coefficient Cd(M) = Cd_ref * f(M): a generic transonic-peak shape (subsonic -> rise -> peak near M~1.1 -> decay).
  This is a textbook-shaped curve, NOT wind-tunnel data for any vehicle.
* Normal force N = q A CNalpha sin(alpha) cos(alpha); CNalpha from a simplified Barrowman model (rocket.cn_alpha()).
* Stagnation-point convective heating, Sutton-Graves: q_dot = k sqrt(rho / R_nose) v^3  [W/m^2].
* Shell stress at a stage base: sigma = N/(2 pi R t) + M/(pi R^2 t)  (thin-walled tube; no buckling, no fatigue).
"""
from __future__ import annotations
import math
import numpy as np

# (Mach, factor on reference Cd)
_CD_TABLE = np.array([[0.0, 1.0], [0.6, 1.0], [0.9, 1.25], [1.05, 1.9], [1.2, 1.8], [2.0, 1.35], [3.0, 1.1], [5.0, 1.0], [10.0, 0.95], [30.0, 0.9]])
GAS = {"Earth": (1.4, 287.05), "Mars": (1.3, 188.92), "Venus": (1.29, 188.92)}
SUTTON_GRAVES_K = {"Earth": 1.7415e-4, "Mars": 1.9027e-4, "Venus": 1.896e-4}   # SI, W s^3 / ... (Earth value from Sutton & Graves 1971)


def cd_factor(mach: float) -> float:
    return float(np.interp(mach, _CD_TABLE[:, 0], _CD_TABLE[:, 1]))


def temperature(body, alt_m: float) -> float:
    h = max(0.0, alt_m) / 1000.0
    if body.name == "Earth":     # US Standard Atmosphere 1976, geopotential layers (approx. with geometric altitude)
        if h <= 11: return 288.15 - 6.5 * h
        if h <= 20: return 216.65
        if h <= 32: return 216.65 + 1.0 * (h - 20)
        if h <= 47: return 228.65 + 2.8 * (h - 32)
        if h <= 51: return 270.65
        if h <= 71: return 270.65 - 2.8 * (h - 51)
        if h <= 86: return 214.65 - 2.0 * (h - 71)
        return 186.95
    if body.name == "Venus": return max(250.0, 737.0 - 8.0 * h)
    return float(body.surface_temp_k or 210.0)


def speed_of_sound(body, alt_m: float) -> float:
    g, R = GAS.get(body.name, (1.3, 188.92))
    return math.sqrt(g * R * temperature(body, alt_m))


def stagnation_heat_flux(body, rho: float, v: float, nose_radius_m: float) -> float:
    k = SUTTON_GRAVES_K.get(body.name, 1.75e-4)
    return k * math.sqrt(max(rho, 0.0) / max(nose_radius_m, 1e-3)) * v ** 3


def normal_force(q: float, area: float, cn_alpha: float, alpha_rad: float) -> float:
    """Normal force magnitude; angles beyond 90 deg are folded (a body flying backwards still feels a restoring cross-flow force)."""
    a = alpha_rad if alpha_rad <= math.pi / 2 else math.pi - alpha_rad
    return q * area * cn_alpha * math.sin(a) * math.cos(a)
