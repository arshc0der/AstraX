"""Headless simulation engine (no Qt / OpenGL imports). Everything physical lives here.

Model summary (documented assumptions - see docs/PHYSICS.md):
  * N-body Newtonian gravity between all bodies (point masses, softening none). The rocket is a
    test particle: it feels every body's gravity but does not perturb them.
  * Variable mass: dm/dt = -F_vac / (Isp_vac * g0) per active engine group, exact over a step.
  * Thrust varies with ambient pressure: F = mdot * g0 * Isp(p), Isp(p) linear between vac and sea level.
  * Drag: F = 0.5 rho Cd A |v_air|^2 along -v_air; air co-rotates with the body. Lift not modelled.
  * Guidance (direction) and throttle are held constant over each integration step (zero-order hold).
  * Frame: barycentric ecliptic J2000 inertial; spin axes simplified (see bodies.py).
Integrators: 'rk4' (fixed), 'dopri5' (adaptive RK 5(4)), 'verlet' (velocity Verlet, symplectic).
"""
from __future__ import annotations
import math, time, copy
from dataclasses import dataclass, field, asdict
import numpy as np
from .constants import G, G0, DEG
from . import integrators as integ
from .atmosphere import density, pressure
from .bodies import SolarSystem
from .orbital import state_to_elements
from .rocket import Rocket, default_rocket

P_SL = 101325.0


@dataclass
class LaunchConfig:
    body: str = "Earth"
    lat_deg: float = 28.5
    lon_deg: float = -80.6
    site_altitude_m: float = 0.0
    start_mode: str = "pad"            # pad | orbit
    orbit_altitude_m: float = 300e3    # for start_mode == orbit
    heading_deg: float = 90.0          # azimuth from north (90 = east)
    target_body: str = "Moon"
    extra_velocity_mps: tuple = (0.0, 0.0, 0.0)   # added inertial velocity (ecliptic), m/s


@dataclass
class Phase:
    """One segment of the flight plan. The phase ends when ANY `until` condition is met."""
    name: str = "Phase"
    mode: str = "hold"                 # hold | fixed_local | pitch_program | gravity_turn | prograde | retrograde |
                                       # radial_out | radial_in | normal | antinormal | coast
    throttle: float = 1.0
    pitch_deg: float = 90.0
    heading_deg: float = 90.0
    pitch_table: list = field(default_factory=list)   # [[t_s, pitch_deg], ...] relative to phase start
    ref: str = "dominant"              # reference body for prograde etc. ('dominant' or a body name)
    target_alt_m: float = 0.0          # used by mode 'ascent_hold'
    until: dict = field(default_factory=dict)         # duration_s, dv_mps, apoapsis_alt_m, periapsis_alt_m,
                                                      # at_apoapsis, burnout, altitude_m, speed_mps


@dataclass
class SimConfig:
    method: str = "rk4"                # rk4 | dopri5 | verlet
    dt_mode: str = "fixed"             # fixed | auto
    dt_s: float = 0.05
    dt_min_s: float = 0.005
    dt_max_s: float = 600.0
    rtol: float = 1e-10                # dopri5 only
    landing_speed_mps: float = 10.0    # max relative speed counted as a soft landing
    record_interval_s: float = 1.0


class Simulation:
    def __init__(self, system: SolarSystem | None = None, rocket: Rocket | None = None,
                 launch: LaunchConfig | None = None, plan: list | None = None,
                 config: SimConfig | None = None):
        self.system = system or SolarSystem()
        self.rocket = copy.deepcopy(rocket or default_rocket())
        self.launch = launch or LaunchConfig()
        self.plan = plan if plan is not None else []
        self.cfg = config or SimConfig()
        self.events: list[tuple[float, str]] = []
        self.reset()

    # ------------------------------------------------------------------ setup
    def reset(self):
        self.t = 0.0                    # s since epoch (J2000)
        self.met = 0.0                  # mission elapsed time (s)
        self.bp, self.bv = self.system.initial_state()
        self.gm = np.array([b.gm for b in self.system.bodies])
        self.radii = np.array([b.radius_m for b in self.system.bodies])
        self.names = [b.name for b in self.system.bodies]
        self.events = []
        self.stages = copy.deepcopy(self.rocket.stages)
        self.jettisoned = []
        self.m = self.rocket.total_mass()
        self.ref_area = self.rocket.reference_area_m2
        self.status = "PAD"
        self.throttle = 0.0
        self.direction = np.array([0.0, 0.0, 1.0])
        self.script_ctrl = None          # (throttle, pitch_deg, heading_deg) set by the user's Python flight script
        self.phase_idx = -1; self.phase_t0 = 0.0; self.phase_dv0 = 0.0; self.dv_spent = 0.0
        self.last_accel = np.zeros(3); self.last_thrust = 0.0; self.last_drag = 0.0
        self.max_q = 0.0; self.max_g = 0.0; self.steps = 0; self.rejected = 0; self._h_try = self.cfg.dt_s
        self._prev_rad_speed = None
        li = self.system.index(self.launch.body); self.li = li
        self._site_body_vec = self._site_vector_bodyframe()
        if self.launch.start_mode == "orbit":
            self._place_in_orbit()
        else:
            self._hold_on_surface()
        self._log(f"Initialised: {self.rocket.name}, launch from {self.launch.body}, mode {self.launch.start_mode}")
        if self.plan: self._enter_phase(0)

    def _log(self, msg):
        self.events.append((self.t, msg))

    # ------------------------------------------------------- body rotation helpers
    def _body_frame(self, i):
        b = self.system.bodies[i]; z = b.spin_axis()
        x = np.array([1.0, 0, 0]) - z * z[0]; x /= np.linalg.norm(x); y = np.cross(z, x)
        return np.column_stack([x, y, z])

    def _site_vector_bodyframe(self):
        la, lo = self.launch.lat_deg * DEG, self.launch.lon_deg * DEG
        return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])

    def _rot_z(self, th):
        c, s = math.cos(th), math.sin(th); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    def surface_state(self, i, unit_body, radius, t=None):
        """Inertial (pos, vel) of a body-fixed point (unit vector in body frame, radius from centre)."""
        t = self.t if t is None else t
        b = self.system.bodies[i]; Bf = self._body_frame(i)
        u = Bf @ self._rot_z(b.omega * t) @ unit_body
        r_rel = u * radius
        w = b.omega * b.spin_axis()
        return self.bp[i] + r_rel, self.bv[i] + np.cross(w, r_rel)

    def local_frame(self, i, pos):
        """(up, north, east) unit vectors at pos above body i."""
        b = self.system.bodies[i]; up = pos - self.bp[i]; up /= np.linalg.norm(up)
        z = b.spin_axis() if b.omega != 0 or True else np.array([0, 0, 1.0])
        east = np.cross(z, up); n = np.linalg.norm(east)
        east = east / n if n > 1e-9 else np.array([0, 1.0, 0]); north = np.cross(up, east)
        return up, north, east

    def _hold_on_surface(self):
        R = self.radii[self.li] + self.launch.site_altitude_m
        self.rp, self.rv = self.surface_state(self.li, self._site_body_vec, R)

    def _place_in_orbit(self):
        R = self.radii[self.li] + self.launch.orbit_altitude_m
        pos, _ = self.surface_state(self.li, self._site_body_vec, R)
        self.rp = pos; up, north, east = self.local_frame(self.li, pos)
        vc = math.sqrt(self.gm[self.li] / R); h = self.launch.heading_deg * DEG
        self.rv = self.bv[self.li] + vc * (math.cos(h) * north + math.sin(h) * east) + np.array(self.launch.extra_velocity_mps)
        self.status = "FLYING"; self.direction = self.rv - self.bv[self.li]
        self.direction /= np.linalg.norm(self.direction)

    # ----------------------------------------------------------------- queries
    def dominant_index(self, pos=None):
        pos = self.rp if pos is None else pos
        d2 = ((self.bp - pos) ** 2).sum(1)
        return int(np.argmax(self.gm / d2))

    def atmosphere_at(self, pos, bp=None):
        """(body index, altitude, density, pressure) for the atmosphere the point is inside, else None."""
        bp = self.bp if bp is None else bp
        for i, b in enumerate(self.system.bodies):
            if b.atmosphere is None: continue
            alt = np.linalg.norm(pos - bp[i]) - b.radius_m
            if alt < b.atmosphere.top_altitude_m:
                return i, alt, density(b, alt), pressure(b, alt)
        return None

    def active_group(self):
        boosters = [s for s in self.stages if s.kind == "booster" and s.propellant_kg > 0]
        core = next((s for s in self.stages if s.kind == "core"), None)
        group = list(boosters)
        if core is not None and core.propellant_kg > 0: group.append(core)
        return group

    def engine_params(self, throttle):
        """(F_vac [N], mdot [kg/s], Isp_vac_eff, Isp_sl_eff) of the active group at given throttle."""
        F = md = 0.0; fs = 0.0
        for s in self.active_group():
            n = s.booster_count if s.kind == "booster" else 1
            F += s.engine.total_thrust_vac * n; md += s.engine.mdot * n; fs += s.engine.thrust_sl * n
        F *= throttle; md *= throttle; fs *= throttle
        if md <= 0: return 0.0, 0.0, 0.0, 0.0
        return F, md, F / (md * G0), fs / (md * G0)

    # --------------------------------------------------------------- dynamics
    def _body_acc(self, bp):
        """N-body accelerations of all bodies, vectorised: a_i = sum_j GM_j (r_j - r_i)/|r_ij|^3."""
        d = bp[None, :, :] - bp[:, None, :]
        r2 = (d ** 2).sum(-1); np.fill_diagonal(r2, 1.0)
        inv3 = r2 ** -1.5; np.fill_diagonal(inv3, 0.0)
        return (d * (self.gm[None, :, None] * inv3[:, :, None])).sum(1)

    def _rocket_forces(self, t, bp, bv, rp, rv, m, dirn, throttle, F_vac, mdot, isp_v, isp_s):
        """Acceleration of the rocket (m/s^2) + diagnostic (thrust N, drag N)."""
        d = bp - rp; r2 = (d ** 2).sum(1)
        acc = (d * (self.gm / r2 ** 1.5)[:, None]).sum(0)
        thrust = drag = 0.0
        atm = self.atmosphere_at(rp, bp)
        if mdot > 0:
            p = atm[3] if atm else 0.0
            isp = isp_v - (isp_v - isp_s) * min(1.0, p / P_SL)
            thrust = mdot * G0 * isp
            acc = acc + dirn * (thrust / m)
        if atm:
            i, alt, rho, _ = atm; b = self.system.bodies[i]
            rel = rp - bp[i]; w = b.omega * b.spin_axis()
            v_air = rv - bv[i] - np.cross(w, rel); sp = np.linalg.norm(v_air)
            if sp > 0 and rho > 0:
                cd = self.rocket.cd
                drag = 0.5 * rho * cd * self.ref_area * sp * sp
                acc = acc - (drag / m) * (v_air / sp)
        return acc, thrust, drag

    def _deriv_factory(self, dirn, throttle, F_vac, mdot, isp_v, isp_s):
        N = len(self.gm)
        def f(t, y):
            bp = y[:3 * N].reshape(N, 3); bv = y[3 * N:6 * N].reshape(N, 3)
            rp = y[6 * N:6 * N + 3]; rv = y[6 * N + 3:6 * N + 6]; m = y[-1]
            ba = self._body_acc(bp)
            ra, _, _ = self._rocket_forces(t, bp, bv, rp, rv, m, dirn, throttle, F_vac, mdot, isp_v, isp_s)
            return np.concatenate([bv.ravel(), ba.ravel(), rv, ra, [-mdot]])
        return f

    def _pack(self):
        return np.concatenate([self.bp.ravel(), self.bv.ravel(), self.rp, self.rv, [self.m]])

    def _unpack(self, y):
        N = len(self.gm)
        self.bp = y[:3 * N].reshape(N, 3).copy(); self.bv = y[3 * N:6 * N].reshape(N, 3).copy()
        self.rp = y[6 * N:6 * N + 3].copy(); self.rv = y[6 * N + 3:6 * N + 6].copy(); self.m = float(y[-1])

    def _integrate(self, h, dirn, throttle, F_vac, mdot, isp_v, isp_s):
        N = len(self.gm)
        if self.cfg.method == "verlet":
            m0 = self.m; t0 = self.t
            x0 = np.concatenate([self.bp.ravel(), self.rp]); v0 = np.concatenate([self.bv.ravel(), self.rv])
            bv_frozen, rv_frozen = self.bv.copy(), self.rv.copy()
            def acc(t, x):
                bp = x[:3 * N].reshape(N, 3); rp = x[3 * N:]
                ba = self._body_acc(bp); mm = m0 - mdot * (t - t0)
                ra, _, _ = self._rocket_forces(t, bp, bv_frozen, rp, rv_frozen, mm, dirn, throttle, F_vac, mdot, isp_v, isp_s)
                return np.concatenate([ba.ravel(), ra])
            x1, v1 = integ.velocity_verlet(acc, x0, v0, h, t0)
            self.bp = x1[:3 * N].reshape(N, 3); self.rp = x1[3 * N:]
            self.bv = v1[:3 * N].reshape(N, 3); self.rv = v1[3 * N:]; self.m = m0 - mdot * h
        else:
            f = self._deriv_factory(dirn, throttle, F_vac, mdot, isp_v, isp_s); y = self._pack()
            if self.cfg.method == "dopri5":
                scale = np.concatenate([np.full(6 * N + 3, 1.0), np.full(3, 1e-6), [1e-3]])
                scale[3 * N:6 * N] = 1e-6
                y, self._h_try, n, rej = integ.dopri5_advance(f, self.t, y, h, self._h_try, self.cfg.rtol, 1.0, 1e-6, scale)
                self.steps += n - 1; self.rejected += rej
            else:
                y = integ.rk4(f, self.t, y, h)
            self._unpack(y)
        self.t += h
        self.steps += 1

    # --------------------------------------------------------------- guidance
    def _ref_velocity(self, ref):
        if ref == "dominant": i = self.dominant_index()
        else: i = self.system.index(ref)
        return i, self.rv - self.bv[i], self.rp - self.bp[i]

    def _guidance(self, ph: Phase):
        """Return (unit thrust direction, throttle) for the current phase."""
        if ph is None or ph.mode == "coast":
            return self.direction, 0.0
        i = self.dominant_index(); up, north, east = self.local_frame(i, self.rp)
        tp = self.t - self.phase_t0
        def local(pitch, hdg):
            p, h = pitch * DEG, hdg * DEG
            return math.sin(p) * up + math.cos(p) * (math.cos(h) * north + math.sin(h) * east)
        m = ph.mode
        if m == "fixed_local": d = local(ph.pitch_deg, ph.heading_deg)
        elif m == "pitch_program":
            tab = sorted(ph.pitch_table) or [[0, ph.pitch_deg]]
            pitch = float(np.interp(tp, [x[0] for x in tab], [x[1] for x in tab]))
            d = local(pitch, ph.heading_deg)
        elif m == "gravity_turn":
            # follow the SURFACE-relative velocity (air-relative): inertial velocity includes planet spin
            b_ = self.system.bodies[i]; w_ = b_.omega * b_.spin_axis()
            v = self.rv - self.bv[i] - np.cross(w_, self.rp - self.bp[i]); sp = np.linalg.norm(v)
            d = v / sp if sp > 30.0 else up
        elif m == "ascent_hold":
            # closed-loop insertion: choose pitch so vertical speed is steered toward a profile that reaches
            # target_alt_m with ~zero vertical speed (gravity-relief aware). Simplified, not optimal guidance.
            rel_r = self.rp - self.bp[i]; r = np.linalg.norm(rel_r); rel_v = self.rv - self.bv[i]
            vr = float(np.dot(rel_v, up)); vh_vec = rel_v - vr * up; vh = np.linalg.norm(vh_vec)
            hor = vh_vec / vh if vh > 1.0 else east
            alt = r - self.radii[i]; vr_cmd = float(np.clip(0.02 * (ph.target_alt_m - alt), 0.0, 400.0))
            a_v = (vr_cmd - vr) / 10.0
            g_eff = self.gm[i] / r ** 2 - vh ** 2 / r
            F, md, iv, _ = self.engine_params(1.0); a_T = F / self.m if self.m > 0 else 1.0
            sin_t = float(np.clip((a_v + g_eff) / max(a_T, 1e-6), -0.3, 1.0))
            d = sin_t * up + math.sqrt(1 - sin_t ** 2) * hor
        elif m in ("prograde", "retrograde", "normal", "antinormal", "radial_out", "radial_in"):
            ri, v, r = self._ref_velocity(ph.ref); sp = np.linalg.norm(v)
            vh = v / sp if sp > 1e-9 else self.direction
            rh = r / np.linalg.norm(r); nrm = np.cross(r, v); nn = np.linalg.norm(nrm)
            nrm = nrm / nn if nn > 1e-12 else up
            d = {"prograde": vh, "retrograde": -vh, "normal": nrm, "antinormal": -nrm,
                 "radial_out": rh, "radial_in": -rh}[m]
        else: d = self.direction
        n = np.linalg.norm(d); d = d / n if n > 0 else self.direction
        return d, float(max(0.0, min(1.0, ph.throttle)))

    def _enter_phase(self, k):
        self.phase_idx = k
        if k < len(self.plan):
            self.phase_t0 = self.t; self.phase_dv0 = self.dv_spent
            self._log(f"Phase {k + 1}: {self.plan[k].name} ({self.plan[k].mode})")
            self._prev_rad_speed = None

    def _phase_done(self, ph: Phase):
        u = ph.until
        if not u: return False
        i = self.dominant_index(); rel_r = self.rp - self.bp[i]; rel_v = self.rv - self.bv[i]
        r = np.linalg.norm(rel_r); alt = r - self.radii[i]
        if "duration_s" in u and self.t - self.phase_t0 >= u["duration_s"]: return True
        if "dv_mps" in u and self.dv_spent - self.phase_dv0 >= u["dv_mps"]: return True
        if "altitude_m" in u and alt >= u["altitude_m"]: return True
        if "speed_mps" in u and np.linalg.norm(rel_v) >= u["speed_mps"]: return True
        if u.get("burnout") and not self.active_group(): return True
        if "stages_jettisoned" in u and len(self.jettisoned) >= u["stages_jettisoned"]: return True
        if "apoapsis_alt_m" in u or "periapsis_alt_m" in u:
            el = state_to_elements(rel_r, rel_v, self.gm[i])
            if "apoapsis_alt_m" in u and el["e"] < 1 and el["ra"] - self.radii[i] >= u["apoapsis_alt_m"]: return True
            if "periapsis_alt_m" in u and el["rp"] - self.radii[i] >= u["periapsis_alt_m"] and el["e"] < 1.0: return True
        if u.get("at_apoapsis"):
            rr = float(np.dot(rel_r, rel_v) / r)
            if self._prev_rad_speed is not None and self._prev_rad_speed > 0 >= rr: return True
            self._prev_rad_speed = rr
        return False

    # ------------------------------------------------------------- stepping
    def auto_dt(self):
        N = len(self.gm); i = self.dominant_index()
        r = np.linalg.norm(self.rp - self.bp[i]); w = math.sqrt(self.gm[i] / r ** 3)
        dt = 0.02 / w
        atm = self.atmosphere_at(self.rp)
        if atm:
            sp = max(1.0, np.linalg.norm(self.rv - self.bv[atm[0]])); H = self.system.bodies[atm[0]].atmosphere.scale_height_m
            dt = min(dt, 0.05 * H / sp)
        if self.throttle > 0: dt = min(dt, 0.1)
        if self.status == "PAD": dt = min(dt, 0.05)
        return float(max(self.cfg.dt_min_s, min(self.cfg.dt_max_s, dt)))

    def step(self, dt=None):
        """Advance by (up to) dt seconds. Returns the time actually advanced."""
        if self.status in ("LANDED", "CRASHED"):
            self._track_surface(); return 0.0
        dt = dt or (self.auto_dt() if self.cfg.dt_mode == "auto" else self.cfg.dt_s)
        ph = self.plan[self.phase_idx] if 0 <= self.phase_idx < len(self.plan) else None
        # phase transitions
        while ph is not None and self._phase_done(ph):
            self._enter_phase(self.phase_idx + 1)
            ph = self.plan[self.phase_idx] if self.phase_idx < len(self.plan) else None
        direction, throttle = self._guidance(ph) if ph is not None else (self.direction, 0.0)
        if self.script_ctrl is not None:          # user flight-computer script overrides the plan
            thr, pit, hdg = self.script_ctrl; i_ = self.dominant_index(); up, north, east = self.local_frame(i_, self.rp)
            p_, h_ = pit * DEG, hdg * DEG
            direction = math.sin(p_) * up + math.cos(p_) * (math.cos(h_) * north + math.sin(h_) * east)
            throttle = float(max(0.0, min(1.0, thr)))
        # time-based staging
        self._auto_stage_time()
        F_vac, mdot, isp_v, isp_s = self.engine_params(throttle)
        # clip step so a stage cutoff happens at a step boundary
        h = dt
        if mdot > 0:
            for s in self.active_group():
                n = s.booster_count if s.kind == "booster" else 1
                md_s = s.engine.mdot * n * throttle
                if md_s > 0:
                    te = s.propellant_kg / md_s
                    if te > 1e-9: h = min(h, te)
        # pad hold: lift off only when thrust exceeds local gravity
        if self.status == "PAD":
            if mdot > 0:
                g = self.gm[self.li] / (self.radii[self.li] + self.launch.site_altitude_m) ** 2
                if F_vac * isp_s / max(isp_v, 1e-9) / self.m > g * 1.0:    # sea-level thrust approx
                    self.status = "FLYING"; self._log(f"LIFTOFF (T/W = {F_vac * isp_s / isp_v / self.m / g:.2f})")
        self.throttle = throttle; self.direction = direction
        self._integrate(h, direction, throttle, F_vac, mdot, isp_v, isp_s)
        # consume propellant & dv bookkeeping
        if mdot > 0:
            for s in self.active_group():
                n = s.booster_count if s.kind == "booster" else 1
                s.propellant_kg = max(0.0, s.propellant_kg - s.engine.mdot * n * throttle * h)
            m_prev = self.m + mdot * h
            self.dv_spent += isp_v * G0 * math.log(m_prev / self.m) if self.m > 0 else 0.0
        self.met += h
        if self.status == "PAD":
            self._hold_on_surface()
        self._post_step(h, throttle, mdot, F_vac, isp_v, isp_s)
        return h

    def _auto_stage_time(self):
        for s in list(self.stages):
            if s.separation == "time" and self.met >= s.separation_time_s and s.kind in ("core", "booster"):
                self.separate(s, "timed")

    def separate(self, stage, reason="manual"):
        if stage not in self.stages: return
        n = stage.booster_count if stage.kind == "booster" else 1
        self.m -= (stage.dry_mass_kg + stage.propellant_kg) * n
        self.stages.remove(stage); self.jettisoned.append(stage)
        self._log(f"STAGE SEPARATION: {stage.name} ({reason}); mass now {self.m:,.0f} kg")
        cores = [s for s in self.stages if s.kind == "core"]
        if cores or self.stages:
            self.ref_area = math.pi * (max([s.diameter_m for s in self.stages if s.kind == "core"] or [self.rocket.nose.base_diameter_m]) / 2) ** 2

    def separate_next(self):
        """Manual staging command: jettison the lowest active core stage (or boosters first)."""
        boosters = [s for s in self.stages if s.kind == "booster"]
        if boosters:
            for b in boosters: self.separate(b, "manual")
        else:
            core = next((s for s in self.stages if s.kind == "core"), None)
            if core and len([s for s in self.stages if s.kind == "core"]) > 1: self.separate(core, "manual")

    def _post_step(self, h, throttle, mdot, F_vac, isp_v, isp_s):
        # automatic burnout staging
        for s in list(self.stages):
            if s.propellant_kg <= 1e-6 and s.separation == "burnout":
                if s.kind == "booster" or len([x for x in self.stages if x.kind == "core"]) > 1:
                    self.separate(s, "burnout")
        # surface contact (any body)
        if self.status == "FLYING":
            d = np.linalg.norm(self.bp - self.rp, axis=1) - self.radii
            i = int(np.argmin(d))
            if d[i] <= 0:
                b = self.system.bodies[i]; rel = self.rp - self.bp[i]
                w = b.omega * b.spin_axis(); vs = np.linalg.norm(self.rv - self.bv[i] - np.cross(w, rel))
                landing = vs <= self.cfg.landing_speed_mps and (self.rocket.cores and True)
                self.status = "LANDED" if landing else "CRASHED"
                self.li = i; Bf = self._body_frame(i)
                u = rel / np.linalg.norm(rel)
                self._site_body_vec = (Bf @ self._rot_z(b.omega * self.t)).T @ u
                self._contact_radius = b.radius_m
                self._log(f"{self.status} on {b.name} at {vs:.1f} m/s relative speed")
                self._track_surface()
                self.throttle = 0.0
        # diagnostics
        atm = self.atmosphere_at(self.rp)
        if atm:
            v = np.linalg.norm(self.rv - self.bv[atm[0]]); q = 0.5 * atm[2] * v * v
            if q > self.max_q: self.max_q = q
        self.last_thrust = 0.0
        if mdot > 0:
            p = atm[3] if atm else 0.0
            self.last_thrust = mdot * G0 * (isp_v - (isp_v - isp_s) * min(1.0, p / P_SL))

    def _track_surface(self):
        self.rp, self.rv = self.surface_state(self.li, self._site_body_vec, getattr(self, "_contact_radius", self.radii[self.li]))

    def advance(self, sim_seconds: float, wall_budget_s: float | None = None, hook=None):
        """Advance by sim_seconds using the configured timestep. Stops early if the wall-clock
        budget runs out (accuracy is never reduced to catch up). Returns (advanced_s, completed)."""
        t_goal = self.t + sim_seconds; w0 = time.perf_counter(); adv0 = self.t
        while self.t < t_goal - 1e-9 and self.status not in ("LANDED", "CRASHED"):
            h = self.step(min(self.auto_dt() if self.cfg.dt_mode == "auto" else self.cfg.dt_s, t_goal - self.t))
            if h <= 0: break
            if hook is not None: hook(self)
            if wall_budget_s is not None and time.perf_counter() - w0 > wall_budget_s:
                return self.t - adv0, False
        if self.status in ("LANDED", "CRASHED"): self._track_surface()
        return self.t - adv0, True

    # ---------------------------------------------------------- diagnostics
    def stability_warnings(self, dt=None):
        """Plain-language warnings if the chosen timestep is unsuitable."""
        dt = dt or self.cfg.dt_s; w = []
        if self.cfg.dt_mode == "auto":
            return w
        i = self.dominant_index(); r = np.linalg.norm(self.rp - self.bp[i]); om = math.sqrt(self.gm[i] / r ** 3)
        th = dt * om
        lim = 0.05 if self.cfg.method != "verlet" else 0.1
        if th > 3 * lim: w.append(f"ERROR: dt={dt:g}s advances {th:.2f} rad of orbit per step around {self.names[i]} - results will be wrong. Reduce dt or use auto.")
        elif th > lim: w.append(f"WARNING: dt={dt:g}s moves {th:.3f} rad of orbit per step around {self.names[i]} (> {lim}). Accuracy degraded.")
        N = len(self.gm)
        for j in range(1, N):
            parent = self.system.bodies[j].parent
            mu = self.gm[self.system.index(parent)] if parent else self.gm[0]
            a = self.system.bodies[j].a
            if a > 0 and dt * math.sqrt(mu / a ** 3) > 0.05: w.append(f"WARNING: dt too large for {self.names[j]}'s orbit.")
        if self.throttle > 0 and dt > 1.0: w.append("WARNING: dt > 1 s while engines burn - staging/guidance are evaluated once per step.")
        atm = self.atmosphere_at(self.rp)
        if atm:
            sp = max(1.0, np.linalg.norm(self.rv - self.bv[atm[0]])); H = self.system.bodies[atm[0]].atmosphere.scale_height_m
            if dt * sp > 0.5 * H: w.append("WARNING: vehicle crosses > half a scale height per step in the atmosphere (drag poorly resolved).")
        return w

    def telemetry(self) -> dict:
        i = self.dominant_index(); b = self.system.bodies[i]
        rel_r = self.rp - self.bp[i]; rel_v = self.rv - self.bv[i]
        r = float(np.linalg.norm(rel_r)); sp = float(np.linalg.norm(rel_v))
        w = b.omega * b.spin_axis(); v_surf = float(np.linalg.norm(rel_v - np.cross(w, rel_r)))
        el = state_to_elements(rel_r, rel_v, self.gm[i])
        grav = self.gm * self.m / np.maximum(((self.bp - self.rp) ** 2).sum(1), 1.0)
        atm = self.atmosphere_at(self.rp)
        rho = atm[2] if atm else 0.0; q = 0.5 * rho * v_surf ** 2
        tgt = self.system.index(self.launch.target_body) if self.launch.target_body in self.names else 0
        dist_t = float(np.linalg.norm(self.rp - self.bp[tgt]) - self.radii[tgt])
        prop = sum(s.propellant_kg * (s.booster_count if s.kind == "booster" else 1) for s in self.stages)
        cap = sum(s.capacity * (s.booster_count if s.kind == "booster" else 1) for s in self.rocket.stages)
        ke = 0.5 * self.m * sp ** 2; pe = -self.m * self.gm[i] / r
        thrust_acc = self.last_thrust / self.m if self.m else 0.0
        gload = thrust_acc / G0
        return dict(t_s=self.t, met_s=self.met, status=self.status, body=b.name, altitude_m=r - b.radius_m,
                    speed_mps=sp, surface_speed_mps=v_surf, mass_kg=self.m, propellant_kg=prop, propellant_fraction=prop / cap if cap else 0.0,
                    thrust_n=self.last_thrust, throttle=self.throttle, accel_thrust_ms2=thrust_acc, g_load=gload,
                    dynamic_pressure_pa=q, air_density=rho, kinetic_j=ke, potential_j=pe, total_energy_j=ke + pe,
                    specific_energy_jkg=el["energy"], sma_m=el["a"], ecc=el["e"], inc_deg=el["inc"],
                    apoapsis_alt_m=(el["ra"] - b.radius_m) if math.isfinite(el["ra"]) else float("inf"),
                    periapsis_alt_m=el["rp"] - b.radius_m, period_s=el["period"],
                    dist_target_m=dist_t, dv_spent_mps=self.dv_spent, gravity_force_dominant_n=float(grav[i]),
                    stage=next((s.name for s in self.stages if s.kind == "core"), "-"),
                    rp_x=float(self.rp[0]), rp_y=float(self.rp[1]), rp_z=float(self.rp[2]),
                    rel_x=float(rel_r[0]), rel_y=float(rel_r[1]), rel_z=float(rel_r[2]),
                    dist_sun_m=float(np.linalg.norm(self.rp - self.bp[0])))

    def total_energy_barycentric(self):
        """Conserved check quantity for the gravity-only N-body system (J): sum KE + PE of bodies."""
        ke = 0.5 * (self.gm / G * (self.bv ** 2).sum(1)).sum()
        pe = 0.0; N = len(self.gm)
        for a in range(N):
            for b in range(a + 1, N):
                pe -= self.gm[a] * self.gm[b] / G / np.linalg.norm(self.bp[a] - self.bp[b])
        return ke + pe
