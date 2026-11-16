"""Numerical integrators. All take a derivative/acceleration callback; no UI dependencies.

rk4            - classical 4th-order Runge-Kutta, fixed step.
dopri5         - Dormand-Prince 5(4) with step-size control (adaptive RK).
velocity_verlet- symplectic 2nd-order, for conservative (gravity-only) systems.
"""
from __future__ import annotations
import numpy as np


def rk4(f, t, y, h):
    k1 = f(t, y); k2 = f(t + h / 2, y + h / 2 * k1)
    k3 = f(t + h / 2, y + h / 2 * k2); k4 = f(t + h, y + h * k3)
    return y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


_C = [0, 1 / 5, 3 / 10, 4 / 5, 8 / 9, 1, 1]
_A = [[], [1 / 5], [3 / 40, 9 / 40], [44 / 45, -56 / 15, 32 / 9],
      [19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729],
      [9017 / 3168, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656],
      [35 / 384, 0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84]]
_B5 = np.array([35 / 384, 0, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84, 0])
_B4 = np.array([5179 / 57600, 0, 7571 / 16695, 393 / 640, -92097 / 339200, 187 / 2100, 1 / 40])


def dopri5_step(f, t, y, h):
    """One Dormand-Prince step. Returns (y5, error_vector)."""
    k = []
    for i in range(7):
        yi = y + h * sum(a * kk for a, kk in zip(_A[i], k)) if i else y
        k.append(f(t + _C[i] * h, yi))
    K = np.array(k)
    y5 = y + h * (_B5 @ K)
    err = h * ((_B5 - _B4) @ K)
    return y5, err


def dopri5_advance(f, t, y, h_total, h_try, rtol=1e-10, atol=1.0, h_min=1e-6, scale=None):
    """Advance exactly h_total using adaptive steps. Returns (y, h_next_guess, n_steps, rejected).

    `scale` optional per-component absolute scale vector (defaults to atol).
    """
    t0, tend = t, t + h_total
    h = min(h_try, h_total); steps = rej = 0
    sc_abs = atol if scale is None else scale
    while t < tend - 1e-12:
        h = min(h, tend - t)
        y_new, err = dopri5_step(f, t, y, h)
        sc = sc_abs + rtol * np.maximum(np.abs(y), np.abs(y_new))
        en = float(np.sqrt(np.mean((err / sc) ** 2)))
        if en <= 1.0 or h <= h_min:
            t += h; y = y_new; steps += 1
        else:
            rej += 1
        fac = 0.9 * (1.0 / max(en, 1e-10)) ** 0.2
        h = max(h_min, h * min(5.0, max(0.2, fac)))
    return y, h, steps, rej


def velocity_verlet(acc, x, v, h, t=0.0):
    """Kick-drift-kick velocity Verlet. acc(t, x) -> a. Returns (x_new, v_new)."""
    a0 = acc(t, x)
    x1 = x + v * h + 0.5 * a0 * h * h
    a1 = acc(t + h, x1)
    return x1, v + 0.5 * (a0 + a1) * h
