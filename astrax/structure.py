"""Simplified structural screening: material table, shell mass and combined-stress check.

Handbook-order-of-magnitude values - verify against MMPDS/ESA data before relying on them.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

# name: (Young's modulus Pa, yield strength Pa, density kg/m^3)
MATERIALS = {
    "Aluminium 2219": (73e9, 340e6, 2840.0),
    "Al-Li 2195": (76e9, 450e6, 2700.0),
    "Stainless steel 304L": (193e9, 240e6, 8000.0),
    "Titanium Ti-6Al-4V": (114e9, 880e6, 4430.0),
    "Carbon composite": (70e9, 600e6, 1600.0),
}


@dataclass
class Limits:
    """Design limits. 'limit' = design allowable; failure happens at limit * fail_factor (or sigma >= yield)."""
    max_q_pa: float = 60e3             # dynamic pressure (fairing / aero loads)
    max_axial_g: float = 6.0           # axial specific force
    max_heat_flux_w_m2: float = 1.0e6  # nose stagnation heat flux the thermal protection can take
    factor_of_safety: float = 1.4      # on yield for the stress check
    fail_factor: float = 1.25          # failure when a load exceeds limit * fail_factor
    max_aoa_deg: float = 25.0          # loss of control threshold with q above 1 kPa


def shell_mass(stage) -> float:
    rho = MATERIALS.get(stage.material, MATERIALS["Al-Li 2195"])[2]
    return rho * 2 * math.pi * (stage.diameter_m / 2) * (stage.wall_thickness_mm / 1000.0) * stage.length_m


def shell_stress(stage, axial_n: float, moment_nm: float) -> float:
    """Peak combined stress (Pa) at the base of the stage's tank section."""
    R = stage.diameter_m / 2; t = max(stage.wall_thickness_mm / 1000.0, 1e-5)
    return abs(axial_n) / (2 * math.pi * R * t) + abs(moment_nm) / (math.pi * R * R * t)


def yield_strength(stage) -> float:
    return MATERIALS.get(stage.material, MATERIALS["Al-Li 2195"])[1]
