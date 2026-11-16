"""Atmospheric density models.

Earth: tabulated US Standard Atmosphere 1976 densities, log-linear interpolation (0-150 km), zero above.
Other bodies: single-scale-height exponential rho = rho0 * exp(-h/H) up to the stated top altitude.
Simplified: no weather, no solar-activity dependence, no temperature/Mach modelling.
"""
from __future__ import annotations
import math
import numpy as np

_US76_H = np.array([0, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150]) * 1000.0
_US76_RHO = np.array([1.225, 0.7364, 0.4135, 0.1948, 0.08891, 0.04008, 0.01841, 0.003996,
                      0.001027, 3.097e-4, 8.283e-5, 1.846e-5, 3.416e-6, 5.604e-7, 2.222e-8, 2.076e-9])
_LOG_RHO = np.log(_US76_RHO)


def density(body, altitude_m: float) -> float:
    atm = body.atmosphere
    if atm is None or altitude_m >= atm.top_altitude_m:
        return 0.0
    h = max(0.0, altitude_m)
    if body.name == "Earth":
        scale = atm.surface_density / 1.225   # honours user edits of surface density
        return scale * float(math.exp(np.interp(h, _US76_H, _LOG_RHO)))
    return atm.surface_density * math.exp(-h / atm.scale_height_m)


def pressure(body, altitude_m: float) -> float:
    """Ambient pressure ~ ideal gas using local density and isothermal scale height (approximate)."""
    atm = body.atmosphere
    if atm is None: return 0.0
    rho0 = atm.surface_density
    return atm.surface_pressure_pa * density(body, altitude_m) / rho0 if rho0 > 0 else 0.0
