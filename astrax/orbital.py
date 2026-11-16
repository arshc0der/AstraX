"""Two-body orbital mechanics helpers (SI units, radians internally unless *_deg)."""
from __future__ import annotations
import math
import numpy as np
from .constants import DEG


def solve_kepler(M: float, e: float, tol: float = 1e-13) -> float:
    """Solve Kepler's equation M = E - e sin E for E (elliptic, 0<=e<1) by Newton iteration."""
    M = (M + math.pi) % (2 * math.pi) - math.pi
    E = M if e < 0.8 else math.pi * (1 if M >= 0 else -1)
    for _ in range(100):
        d = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        E -= d
        if abs(d) < tol:
            break
    return E


def _rot(raan, inc, argp):
    cO, sO, ci, si, cw, sw = (math.cos(raan), math.sin(raan), math.cos(inc), math.sin(inc),
                              math.cos(argp), math.sin(argp))
    return np.array([[cO * cw - sO * sw * ci, -cO * sw - sO * cw * ci, sO * si],
                     [sO * cw + cO * sw * ci, -sO * sw + cO * cw * ci, -cO * si],
                     [sw * si, cw * si, ci]])


def elements_to_state(a, e, inc_deg, raan_deg, argp_deg, m0_deg, mu):
    """Keplerian elements (elliptic) -> (r, v) in the reference (ecliptic) frame."""
    E = solve_kepler(m0_deg * DEG, e)
    nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
    p = a * (1 - e * e)
    r = p / (1 + e * math.cos(nu))
    r_pf = np.array([r * math.cos(nu), r * math.sin(nu), 0.0])
    v_pf = math.sqrt(mu / p) * np.array([-math.sin(nu), e + math.cos(nu), 0.0])
    R = _rot(raan_deg * DEG, inc_deg * DEG, argp_deg * DEG)
    return R @ r_pf, R @ v_pf


def state_to_elements(r, v, mu) -> dict:
    """(r, v) -> classical elements. Works for elliptic and hyperbolic orbits.

    Returns SI + degrees. Keys: a, e, inc, raan, argp, nu, energy, period, rp, ra, h.
    """
    r = np.asarray(r, float); v = np.asarray(v, float)
    rm, vm = np.linalg.norm(r), np.linalg.norm(v)
    h = np.cross(r, v); hm = np.linalg.norm(h)
    evec = np.cross(v, h) / mu - r / rm
    e = np.linalg.norm(evec)
    energy = 0.5 * vm * vm - mu / rm
    a = -mu / (2 * energy) if abs(energy) > 1e-12 else math.inf
    inc = math.acos(max(-1, min(1, h[2] / hm))) if hm > 0 else 0.0
    n = np.array([-h[1], h[0], 0.0]); nm = np.linalg.norm(n)
    raan = math.atan2(n[1], n[0]) % (2 * math.pi) if nm > 1e-12 else 0.0
    if nm > 1e-12 and e > 1e-10:
        argp = math.acos(max(-1, min(1, np.dot(n, evec) / (nm * e))))
        if evec[2] < 0: argp = 2 * math.pi - argp
    else:
        argp = math.atan2(evec[1], evec[0]) % (2 * math.pi) if e > 1e-10 else 0.0
    if e > 1e-10:
        nu = math.acos(max(-1, min(1, np.dot(evec, r) / (e * rm))))
        if np.dot(r, v) < 0: nu = 2 * math.pi - nu
    else:
        nu = 0.0
    rp = hm * hm / mu / (1 + e)
    ra = a * (1 + e) if e < 1 and math.isfinite(a) else math.inf
    period = 2 * math.pi * math.sqrt(a ** 3 / mu) if (a > 0 and math.isfinite(a)) else math.inf
    return dict(a=a, e=e, inc=inc / DEG, raan=raan / DEG, argp=argp / DEG, nu=nu / DEG,
                energy=energy, period=period, rp=rp, ra=ra, h=hm)


def circular_speed(mu, r): return math.sqrt(mu / r)
def escape_speed(mu, r): return math.sqrt(2 * mu / r)


def hohmann(mu, r1, r2) -> dict:
    """Hohmann transfer between circular coplanar orbits: dv1, dv2 (m/s), time of flight (s)."""
    at = 0.5 * (r1 + r2)
    v1 = math.sqrt(mu / r1); v2 = math.sqrt(mu / r2)
    vt1 = math.sqrt(mu * (2 / r1 - 1 / at)); vt2 = math.sqrt(mu * (2 / r2 - 1 / at))
    return dict(dv1=vt1 - v1, dv2=v2 - vt2, total=abs(vt1 - v1) + abs(v2 - vt2),
                tof=math.pi * math.sqrt(at ** 3 / mu))
