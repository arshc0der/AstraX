"""Lambert's problem (universal-variable method, Bate-Mueller-White / Curtis): the transfer orbit between two position
vectors in a given time. Used by the launch-window planner. Single revolution, prograde or retrograde."""
from __future__ import annotations
import math
import numpy as np


def _C(z):
    if z > 1e-8: return (1 - math.cos(math.sqrt(z))) / z
    if z < -1e-8: return (math.cosh(math.sqrt(-z)) - 1) / (-z)
    return 0.5 - z / 24 + z * z / 720


def _S(z):
    if z > 1e-8: s = math.sqrt(z); return (s - math.sin(s)) / s ** 3
    if z < -1e-8: s = math.sqrt(-z); return (math.sinh(s) - s) / s ** 3
    return 1 / 6 - z / 120 + z * z / 5040


def lambert(r1, r2, tof, mu, prograde=True, max_iter=200):
    """Return (v1, v2) velocity vectors at r1 and r2 for the transfer taking `tof` seconds. Raises ValueError if no solution."""
    r1 = np.asarray(r1, float); r2 = np.asarray(r2, float); a1, a2 = np.linalg.norm(r1), np.linalg.norm(r2)
    cosd = float(np.clip(np.dot(r1, r2) / (a1 * a2), -1, 1)); dnu = math.acos(cosd); cz = np.cross(r1, r2)[2]
    if (prograde and cz < 0) or (not prograde and cz >= 0): dnu = 2 * math.pi - dnu
    A = math.sin(dnu) * math.sqrt(a1 * a2 / (1 - math.cos(dnu)))
    if abs(A) < 1e-12: raise ValueError("degenerate geometry (180 deg or 0 deg transfer)")
    y = lambda z: a1 + a2 + A * (z * _S(z) - 1) / math.sqrt(_C(z))
    F = lambda z: (y(z) / _C(z)) ** 1.5 * _S(z) + A * math.sqrt(max(y(z), 0.0)) - math.sqrt(mu) * tof
    lo, hi = -4 * math.pi ** 2 * 4, (2 * math.pi) ** 2 - 1e-6
    while y(lo) <= 0 and lo < hi: lo += 1.0
    if y(lo) <= 0: raise ValueError("no solution")
    if F(lo) > 0: raise ValueError("time of flight too short for a solution on this geometry")
    if F(hi) < 0 and y(hi) > 0: raise ValueError("time of flight too long (needs multiple revolutions)")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        if y(mid) <= 0: lo = mid; continue
        if F(mid) < 0: lo = mid
        else: hi = mid
        if hi - lo < 1e-12: break
    z = 0.5 * (lo + hi); yz = y(z)
    f = 1 - yz / a1; g = A * math.sqrt(yz / mu); gd = 1 - yz / a2
    return (r2 - f * r1) / g, (gd * r2 - r1) / g
