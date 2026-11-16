"""Celestial body reference data + editable runtime copies.

REFERENCE DATA (never silently modified - the editable copy is separate):
  * GM values:  JPL Solar System Dynamics, "Planetary Physical Parameters"
                (ssd.jpl.nasa.gov/planets/phys_par.html); IAU 2015 nominal values for the Sun.
  * Mean radii: same JPL table / IAU WGCCRE 2015 report.
  * Orbital elements: E. M. Standish, "Keplerian Elements for Approximate Positions of the
                Major Planets" (JPL), Table 1, valid 1800-2050 AD, epoch J2000.0, ecliptic/equinox J2000.
  * Moon elements: approximate osculating J2000 values (Meeus, Astronomical Algorithms).
  LIMITATIONS: mean elements are NOT an ephemeris (errors of arcminutes to a few
  arcminutes for inner planets, more for outer planets). Rotation poles are simplified: the
  spin axis is the ecliptic north tilted by the axial tilt about the +X axis.
  PLEASE verify the numbers against the cited tables before publishing results.
"""
from __future__ import annotations
import copy
import math
from dataclasses import dataclass, field, asdict
import numpy as np
from .constants import G, AU, DEG, DAY
from .orbital import elements_to_state

EPOCH = "J2000.0 (JD 2451545.0)"


@dataclass
class Atmosphere:
    surface_pressure_pa: float
    surface_density: float      # kg/m^3
    scale_height_m: float
    top_altitude_m: float
    composition: str
    surface_temp_k: float


@dataclass
class Body:
    name: str
    gm: float                   # m^3/s^2  (gravitational parameter, edit this or mass)
    radius_m: float
    color: tuple
    rotation_period_s: float    # sidereal; negative = retrograde
    axial_tilt_deg: float
    parent: str | None = None   # None = heliocentric
    # Keplerian elements (a[m], e, i, Omega, omega, M0 in deg) about parent at epoch
    a: float = 0.0
    e: float = 0.0
    inc: float = 0.0
    raan: float = 0.0
    argp: float = 0.0
    m0: float = 0.0
    atmosphere: Atmosphere | None = None
    source: str = ""
    surface_temp_k: float | None = None

    # ---- derived properties ----
    @property
    def mass(self) -> float:
        return self.gm / G

    @property
    def mean_density(self) -> float:
        return self.mass / (4.0 / 3.0 * math.pi * self.radius_m ** 3)

    @property
    def surface_gravity(self) -> float:
        return self.gm / self.radius_m ** 2

    @property
    def escape_velocity(self) -> float:
        return math.sqrt(2 * self.gm / self.radius_m)

    @property
    def orbital_period_s(self) -> float | None:
        return None  # filled in by SolarSystem (needs parent GM)

    def spin_axis(self) -> np.ndarray:
        t = self.axial_tilt_deg * DEG
        return np.array([0.0, -math.sin(t), math.cos(t)])

    @property
    def omega(self) -> float:
        return 0.0 if self.rotation_period_s == 0 else 2 * math.pi / self.rotation_period_s


def _mk(name, gm, r_km, color, rot_h, tilt, a_au, e, inc, L, varpi, node, src, **kw):
    # Standish gives mean longitude L and longitude of perihelion varpi: M = L - varpi, argp = varpi - node
    return Body(name, gm, r_km * 1000.0, color, rot_h * 3600.0, tilt, None, a_au * AU, e, inc,
                node, varpi - node, (L - varpi) % 360.0, source=src, **kw)

_SRC = "GM/radius: JPL SSD planetary physical parameters; elements: Standish (JPL) approx. mean elements, J2000"

REFERENCE_BODIES: list[Body] = [
    Body("Sun", 1.32712440018e20, 695700e3, (1.0, 0.85, 0.3, 1), 609.12 * 3600, 7.25,
         source="GM: IAU 2015 nominal; radius: IAU 2015; rotation: carrington-ish synodic-free sidereal approx"),
    _mk("Mercury", 2.2031868551e13, 2439.4, (0.6, 0.58, 0.55, 1), 1407.6, 0.034,
        0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593, _SRC),
    _mk("Venus", 3.24858592e14, 6051.8, (0.9, 0.8, 0.55, 1), -5832.5, 177.36,
        0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255, _SRC,
        atmosphere=Atmosphere(9.2e6, 65.0, 15900.0, 250e3, "96.5% CO2, 3.5% N2", 737.0)),
    # Earth-Moon barycentre elements are used to place Earth and Moon (see SolarSystem)
    _mk("Earth", 3.986004418e14, 6371.0, (0.2, 0.45, 1.0, 1), 23.9344696, 23.4393,
        1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0, _SRC,
        atmosphere=Atmosphere(101325.0, 1.225, 8500.0, 150e3, "78% N2, 21% O2, 0.9% Ar", 288.15)),
    Body("Moon", 4.9028000e12, 1737.4e3, (0.75, 0.75, 0.75, 1), 655.72 * 3600, 6.68, "Earth",
         384.4e6, 0.0549, 5.145, 125.08, 318.15, 135.27,
         source="GM/radius: JPL; elements: approx osculating J2000 (Meeus)"),
    _mk("Mars", 4.282837e13, 3389.5, (0.9, 0.35, 0.15, 1), 24.6229, 25.19,
        1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891, _SRC,
        atmosphere=Atmosphere(610.0, 0.020, 11100.0, 80e3, "95% CO2, 2.8% N2, 2% Ar", 210.0)),
    _mk("Jupiter", 1.26686534e17, 69911.0, (0.85, 0.7, 0.55, 1), 9.925, 3.13,
        5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909, _SRC),
    _mk("Saturn", 3.7931187e16, 58232.0, (0.85, 0.78, 0.5, 1), 10.656, 26.73,
        9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448, _SRC),
    _mk("Uranus", 5.793939e15, 25362.0, (0.5, 0.85, 0.9, 1), -17.24, 97.77,
        19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503, _SRC),
    _mk("Neptune", 6.836529e15, 24622.0, (0.25, 0.35, 0.95, 1), 16.11, 28.32,
        30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574, _SRC),
]
# Mean surface temperatures (K), JPL/NASA fact sheets (approximate)
_TEMP = {"Sun": 5772, "Mercury": 440, "Venus": 737, "Earth": 288, "Moon": 250, "Mars": 210,
         "Jupiter": 165, "Saturn": 134, "Uranus": 76, "Neptune": 72}
for _b in REFERENCE_BODIES:
    _b.surface_temp_k = _TEMP.get(_b.name)
# Uranus tilt 97.77 deg (IAU); Venus 177.36


class SolarSystem:
    """Holds editable bodies, builds initial barycentric state vectors."""

    def __init__(self):
        self.reset_all()

    def reset_all(self):
        self.bodies: list[Body] = copy.deepcopy(REFERENCE_BODIES)

    def reset_body(self, name: str):
        ref = next(b for b in REFERENCE_BODIES if b.name == name)
        i = self.index(name)
        self.bodies[i] = copy.deepcopy(ref)

    def index(self, name: str) -> int:
        for i, b in enumerate(self.bodies):
            if b.name == name:
                return i
        raise KeyError(name)

    def get(self, name: str) -> Body:
        return self.bodies[self.index(name)]

    def is_modified(self, name: str) -> bool:
        ref = next(b for b in REFERENCE_BODIES if b.name == name)
        return asdict(ref) != asdict(self.get(name))

    def orbital_period(self, name: str) -> float | None:
        b = self.get(name)
        if b.a <= 0:
            return None
        parent = self.get(b.parent) if b.parent else self.bodies[0]
        mu = parent.gm + (b.gm if b.parent else 0.0)
        return 2 * math.pi * math.sqrt(b.a ** 3 / mu)

    def initial_state(self):
        """Return (positions Nx3, velocities Nx3) in a barycentric ecliptic-J2000 frame."""
        n = len(self.bodies)
        pos = np.zeros((n, 3)); vel = np.zeros((n, 3))
        sun = self.bodies[0]
        for i, b in enumerate(self.bodies):
            if b.parent is None and b.a > 0:
                mu = sun.gm + (self.get("Moon").gm + b.gm if b.name == "Earth" else b.gm)
                pos[i], vel[i] = elements_to_state(b.a, b.e, b.inc, b.raan, b.argp, b.m0, mu)
        moon = self.get("Moon"); earth = self.get("Earth")
        im, ie = self.index("Moon"), self.index("Earth")
        emb_p, emb_v = pos[ie].copy(), vel[ie].copy()
        rp, rv = elements_to_state(moon.a, moon.e, moon.inc, moon.raan, moon.argp, moon.m0,
                                   earth.gm + moon.gm)
        mt = earth.gm + moon.gm
        pos[ie] = emb_p - rp * moon.gm / mt; vel[ie] = emb_v - rv * moon.gm / mt
        pos[im] = emb_p + rp * earth.gm / mt; vel[im] = emb_v + rv * earth.gm / mt
        gm = np.array([b.gm for b in self.bodies])
        # move to barycentre (zero total momentum)
        pos -= (gm[:, None] * pos).sum(0) / gm.sum()
        vel -= (gm[:, None] * vel).sum(0) / gm.sum()
        return pos, vel
