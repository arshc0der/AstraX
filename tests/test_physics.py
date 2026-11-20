"""Unit + integration tests (stdlib unittest; run: python -m unittest discover -s tests -v)."""
import math, os, sys, tempfile, unittest
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from astrax.constants import G, G0
from astrax import orbital, integrators as integ
from astrax.bodies import SolarSystem, REFERENCE_BODIES
from astrax.rocket import Rocket, Stage, Engine, default_rocket
from astrax.rocket_mesh import build_rocket_parts, nose_profile, load_obj, export_obj
from astrax.simulation import Simulation, LaunchConfig, Phase, SimConfig
from astrax.missions import earth_leo
from astrax.recorder import Recorder, save_report
from astrax import project, atmosphere
from astrax.runtime import MissionRuntime
from astrax import aero, structure
from astrax.survival import run_survival_test
from astrax import lambert as lam, transfer, reentry, studies, challenges, rocket_library
from astrax.missions import moon_descent
from ui import gpu


class TestOrbital(unittest.TestCase):
    def test_kepler_roundtrip(self):
        mu = 3.986004418e14
        r, v = orbital.elements_to_state(8.0e6, 0.1, 30, 40, 50, 60, mu)
        el = orbital.state_to_elements(r, v, mu)
        for k, ref in zip(("a", "e", "inc", "raan", "argp"), (8.0e6, 0.1, 30, 40, 50)):
            self.assertAlmostEqual(el[k] / ref, 1.0, places=9, msg=k)

    def test_hohmann_leo_geo(self):   # textbook: dv_total ~ 3.89 km/s, tof ~ 5.28 h
        mu = 3.986004418e14; h = orbital.hohmann(mu, 6678e3, 42164e3)
        self.assertAlmostEqual(h["total"], 3.9e3, delta=0.1e3); self.assertAlmostEqual(h["tof"] / 3600, 5.28, delta=0.05)

    def test_circular_period(self):
        mu = 3.986004418e14; r = 7000e3
        self.assertAlmostEqual(2 * math.pi * math.sqrt(r ** 3 / mu), 5828.5, delta=1.0)


class TestIntegrators(unittest.TestCase):
    def _harmonic(self, method, h, T=20.0):
        f = lambda t, y: np.array([y[1], -y[0]]); y = np.array([1.0, 0.0]); t = 0
        while t < T - 1e-12:
            y = integ.rk4(f, t, y, h) if method == "rk4" else integ.dopri5_advance(f, t, y, h, h, 1e-12, 1e-12)[0]; t += h
        return abs(y[0] - math.cos(T))
    def test_rk4_order4(self):
        e1, e2 = self._harmonic("rk4", 0.1), self._harmonic("rk4", 0.05)
        self.assertAlmostEqual(math.log2(e1 / e2), 4.0, delta=0.3)
    def test_dopri_accuracy(self): self.assertLess(self._harmonic("dopri", 0.5), 1e-8)
    def test_verlet_energy_bounded(self):
        acc = lambda t, x: -x; x, v = np.array([1.0]), np.array([0.0]); E0 = 0.5
        for _ in range(100000): x, v = integ.velocity_verlet(acc, x, v, 0.05)
        self.assertLess(abs(0.5 * v[0] ** 2 + 0.5 * x[0] ** 2 - E0), 1e-3)


class TestBodies(unittest.TestCase):
    def test_reference_values(self):
        s = SolarSystem(); e = s.get("Earth")
        self.assertAlmostEqual(e.surface_gravity, 9.82, delta=0.05); self.assertAlmostEqual(e.mean_density, 5514, delta=30)
        self.assertAlmostEqual(s.orbital_period("Earth") / 86400, 365.25, delta=0.1)
        self.assertAlmostEqual(s.orbital_period("Mars") / 86400, 686.98, delta=0.5)
    def test_reset_and_modified(self):
        s = SolarSystem(); s.get("Mars").gm *= 2; self.assertTrue(s.is_modified("Mars"))
        s.reset_body("Mars"); self.assertFalse(s.is_modified("Mars"))
    def test_reference_not_mutated(self):
        s = SolarSystem(); ref = [b.gm for b in REFERENCE_BODIES]; s.get("Earth").gm *= 3
        self.assertEqual(ref, [b.gm for b in REFERENCE_BODIES])
    def test_zero_momentum(self):
        s = SolarSystem(); p, v = s.initial_state(); gm = np.array([b.gm for b in s.bodies])
        self.assertLess(np.linalg.norm((gm[:, None] * v).sum(0)) / gm.sum(), 1e-6)


class TestRocket(unittest.TestCase):
    def test_tsiolkovsky_single_stage(self):
        st = Stage("S", "core", 3, 20, 1000, 9000, 0, Engine(1, 500e3, 300, 280)); r = Rocket("t", [st], 0.0)
        r.nose.mass_kg = 0
        e = r.estimates(); self.assertAlmostEqual(e["delta_v_mps"], 300 * G0 * math.log(10000 / 1000), delta=1.0)
        self.assertAlmostEqual(e["mass_ratio"], 10.0, places=6)
    def test_twr(self):
        r = default_rocket(); e = r.estimates(); self.assertAlmostEqual(e["twr_sl"], e["thrust_sl_n"] / (e["launch_mass_kg"] * G0), places=9)
    def test_json_roundtrip(self):
        r = default_rocket()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.json"); r.save(p); self.assertEqual(Rocket.load(p).to_dict(), r.to_dict())
    def test_mesh_valid_and_responds(self):
        r = default_rocket(); P = build_rocket_parts(r); V = np.vstack([p.vertices for p in P])
        self.assertTrue(np.isfinite(V).all()); h1 = V[:, 2].max()
        for p in P: self.assertTrue(p.faces.max() < len(p.vertices))
        r.stages[1].length_m += 10; V2 = np.vstack([p.vertices for p in build_rocket_parts(r)])
        self.assertAlmostEqual(V2[:, 2].max() - h1, 10.0, places=6)
    def test_obj_roundtrip(self):
        P = build_rocket_parts(default_rocket())
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.obj"); export_obj(P, p); V, F = load_obj(p)
            self.assertEqual(len(V), sum(len(x.vertices) for x in P))
    def test_validation_flags_low_twr(self):
        r = default_rocket(); r.stages[0].engine.count = 1
        self.assertTrue(any("T/W" in w for w in r.validate()))


class TestSimulation(unittest.TestCase):
    def _leo(self, method, dt):
        sim = Simulation(launch=LaunchConfig(start_mode="orbit", orbit_altitude_m=400e3), config=SimConfig(method=method, dt_s=dt))
        r0 = sim.radii[sim.li] + 400e3; T = 2 * math.pi * math.sqrt(r0 ** 3 / sim.gm[sim.li]); sim.advance(2 * T)
        return sim.telemetry(), r0
    def test_circular_orbit_stays_circular(self):
        for m in ("rk4", "dopri5", "verlet"):
            tm, r0 = self._leo(m, 5.0); self.assertLess(tm["ecc"], 1e-6, m); self.assertLess(abs(tm["sma_m"] - r0), 1.0, m)
    def test_nbody_energy_conserved(self):
        sim = Simulation(config=SimConfig(method="rk4", dt_s=600)); sim.launch.start_mode = "orbit"
        E0 = sim.total_energy_barycentric(); sim.advance(86400 * 60)
        self.assertLess(abs(sim.total_energy_barycentric() / E0 - 1), 1e-10)
    def test_earth_year(self):   # Earth returns to ~same heliocentric longitude after one sidereal year
        sim = Simulation(config=SimConfig(method="rk4", dt_s=1800)); i = sim.system.index("Earth")
        r0 = sim.bp[i] - sim.bp[0]; P = sim.system.orbital_period("Earth"); sim.advance(P)
        r1 = sim.bp[i] - sim.bp[0]; ang = math.acos(np.dot(r0, r1) / np.linalg.norm(r0) / np.linalg.norm(r1))
        self.assertLess(ang, 0.02)   # N-body perturbations (Moon, Jupiter...) shift this slightly
    def test_changing_earth_mass_changes_orbit(self):
        s = SolarSystem(); s.get("Earth").gm *= 1.5
        sim = Simulation(system=s, launch=LaunchConfig(start_mode="orbit", orbit_altitude_m=400e3))
        r0 = sim.radii[sim.li] + 400e3; v = np.linalg.norm(sim.rv - sim.bv[sim.li])
        self.assertAlmostEqual(v, math.sqrt(1.5 * 3.986004418e14 / r0), delta=1.0)
    def test_free_fall_hits_surface(self):
        sim = Simulation(launch=LaunchConfig(start_mode="orbit", orbit_altitude_m=100e3), config=SimConfig(dt_mode="auto", failures=False))
        sim.rv = sim.bv[sim.li].copy(); sim.rocket.cd = 0.0     # drop from rest, no drag
        sim.advance(2000); self.assertEqual(sim.status, "CRASHED")
    def test_rocket_equation_in_simulation(self):
        """Vacuum, gravity-free-ish deep space burn: simulated dv must equal Isp*g0*ln(m0/m1)."""
        st = Stage("S", "core", 2, 10, 1000, 4000, 0, Engine(1, 50e3, 300, 300)); r = Rocket("t", [st], 500.0); r.nose.mass_kg = 0
        L = LaunchConfig(body="Earth", start_mode="orbit", orbit_altitude_m=36000e3)
        sim = Simulation(rocket=r, launch=L, plan=[Phase("burn", "prograde", 1.0, until={"burnout": True})], config=SimConfig(dt_s=0.5))
        m0 = sim.m; v0 = np.linalg.norm(sim.rv); T = 4000 / st.engine.mdot
        sim.advance(T * 0.5); self.assertAlmostEqual(sim.dv_spent, 300 * G0 * math.log(m0 / sim.m), delta=1e-6)
        self.assertAlmostEqual(m0 - sim.m, st.engine.mdot * T * 0.5, delta=1e-6)
    def test_stability_warning(self):
        sim = Simulation(launch=LaunchConfig(start_mode="orbit", orbit_altitude_m=400e3), config=SimConfig(dt_s=600))
        self.assertTrue(any(w.startswith("ERROR") for w in sim.stability_warnings()))
    def test_atmosphere_density(self):
        e = SolarSystem().get("Earth"); self.assertAlmostEqual(atmosphere.density(e, 0), 1.225, places=6)
        self.assertAlmostEqual(atmosphere.density(e, 10000), 0.4135, places=4); self.assertEqual(atmosphere.density(e, 200e3), 0.0)
    def test_surface_launch_site_speed(self):   # equatorial rotation speed ~ 465 m/s
        sim = Simulation(launch=LaunchConfig(lat_deg=0.0, lon_deg=0.0)); v = np.linalg.norm(sim.rv - sim.bv[sim.li])
        self.assertAlmostEqual(v, 2 * math.pi * 6371e3 / 86164.1, delta=2.0)
    def test_pad_hold_when_twr_low(self):
        r = default_rocket(); r.stages[0].engine.count = 1
        sim = Simulation(rocket=r, plan=[Phase("up", "fixed_local", 1.0, 90, 90, until={})], config=SimConfig(dt_s=0.1))
        sim.advance(20); self.assertEqual(sim.status, "PAD")
    def test_full_ascent_to_orbit(self):    # integration test of the whole launch workflow
        L, plan = earth_leo(200e3, 6.0); sim = Simulation(launch=L, plan=plan, config=SimConfig(dt_mode="auto"))
        rec = Recorder(5.0)
        while sim.met < 1500 and sim.status in ("PAD", "FLYING") and sim.phase_idx < 4: sim.step(); rec.maybe_record(sim)
        tm = sim.telemetry(); self.assertEqual(sim.status, "FLYING")
        self.assertGreater(tm["periapsis_alt_m"], 150e3); self.assertLess(tm["ecc"], 0.02); self.assertEqual(len(sim.jettisoned), 1)
        with tempfile.TemporaryDirectory() as d:
            rec.export_csv(os.path.join(d, "a.csv")); rec.save_session(os.path.join(d, "s.json"))
            self.assertEqual(len(Recorder.load_session(os.path.join(d, "s.json"))), len(rec))
            save_report(os.path.join(d, "r.md"), sim, rec, default_rocket().estimates(), make_plots=False)
            with open(os.path.join(d, "r.md")) as fh: self.assertIn("SIMULATION RESULTS", fh.read())
    def test_scenario_roundtrip(self):
        L, plan = earth_leo(); s = SolarSystem(); s.get("Mars").gm *= 1.1
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sc.json"); project.save_scenario(p, default_rocket(), L, plan, SimConfig(), s, "t")
            r, L2, plan2, c2, s2, name = project.load_scenario(p)
            self.assertEqual(plan2, plan); self.assertAlmostEqual(s2.get("Mars").gm, s.get("Mars").gm)
            self.assertFalse(s2.is_modified("Earth"))


class TestRuntime(unittest.TestCase):
    def test_script_controls_rocket_and_is_restricted(self):
        sim = Simulation(config=SimConfig(dt_s=0.1)); logs = []; rt = MissionRuntime(sim, logs.append)
        self.assertTrue(rt.compile_script("def mission_loop():\n    rocket.set_pitch(90); rocket.set_thrust(1.0)\n"))
        for _ in range(100): rt.execute_step(); sim.step()
        self.assertEqual(sim.status, "FLYING"); self.assertGreater(sim.telemetry()["altitude_m"], 10)
        self.assertFalse(rt.compile_script("import os\ndef mission_loop():\n    pass\n"))     # imports blocked
    def test_script_without_loop_rejected(self):
        sim = Simulation(); self.assertFalse(MissionRuntime(sim, lambda m: None).compile_script("x = 1"))


def _ascent(rocket=None, steps_until=None, **cfg):
    L, plan = earth_leo(200e3, 6.0); sim = Simulation(rocket=rocket, launch=L, plan=plan, config=SimConfig(dt_mode="auto", **cfg)); return sim


class TestAeroAndSafety(unittest.TestCase):
    def test_speed_of_sound_and_cd_curve(self):
        e = SolarSystem().get("Earth")
        self.assertAlmostEqual(aero.speed_of_sound(e, 0), 340.3, delta=0.5); self.assertAlmostEqual(aero.speed_of_sound(e, 11000), 295.1, delta=0.5)
        self.assertGreater(aero.cd_factor(1.1), aero.cd_factor(0.3)); self.assertGreater(aero.cd_factor(1.1), aero.cd_factor(4.0))   # transonic peak
    def test_sutton_graves_scaling(self):
        e = SolarSystem().get("Earth"); a = aero.stagnation_heat_flux(e, 1e-3, 2000, 0.3)
        self.assertAlmostEqual(aero.stagnation_heat_flux(e, 1e-3, 4000, 0.3) / a, 8.0, places=6)       # ~ v^3
        self.assertAlmostEqual(aero.stagnation_heat_flux(e, 4e-3, 2000, 0.3) / a, 2.0, places=6)       # ~ sqrt(rho)
    def test_shell_stress_hand_calc(self):
        from astrax.rocket import Stage
        st = Stage(diameter_m=2.0, wall_thickness_mm=5.0); sig = structure.shell_stress(st, 1e6, 0.0)
        self.assertAlmostEqual(sig, 1e6 / (2 * math.pi * 1.0 * 0.005), places=3)
    def test_default_rocket_survives_ascent(self):
        sim = _ascent(); last = len(sim.plan) - 1
        while sim.met < 1800 and not sim.terminal() and sim.phase_idx < last: sim.step()
        self.assertEqual(sim.status, "FLYING"); self.assertLess(sim.peak["g_ratio"], 1.0); self.assertLess(sim.peak["q_ratio"], 1.0)
    def test_survival_report_cases(self):
        self.assertTrue(run_survival_test(default_rocket()).survived)
        thin = default_rocket()
        for s in thin.stages: s.wall_thickness_mm = 0.5
        r = run_survival_test(thin); self.assertEqual(r.verdict, "LOST"); self.assertIn("structural", r.reason)
        weak = default_rocket(); weak.stages[0].engine.count = 1; self.assertEqual(run_survival_test(weak).verdict, "NO_LIFTOFF")
        unstable = default_rocket(); unstable.active_control = False; self.assertEqual(run_survival_test(unstable).verdict, "LOST")
    def test_overload_without_protection_destroys(self):
        r = default_rocket(); r.limits.max_q_pa = 15e3
        self.assertEqual(run_survival_test(r, protect=False).verdict, "LOST")
    def test_breakup_creates_debris_and_ends_run(self):
        thin = default_rocket()
        for s in thin.stages: s.wall_thickness_mm = 0.5
        sim = _ascent(thin)
        while not sim.terminal() and sim.met < 300: sim.step()
        self.assertEqual(sim.status, "DESTROYED"); self.assertGreater(len(sim.debris), 20); self.assertTrue(sim.failure_reason)
    def test_engine_out_reduces_thrust(self):
        sim = _ascent(); f0 = sim.engine_params(1.0)[0]; sim.emergency("engine_out"); self.assertAlmostEqual(sim.engine_params(1.0)[0] / f0, 8 / 9, places=9)
    def test_fuel_leak_loses_mass(self):
        sim = _ascent(); sim.emergency("fuel_leak", 500.0)
        for _ in range(200): sim.step(0.1)
        self.assertLess(sim.stages[0].propellant_kg, 395700 - 500 * 15)   # leak + burn both drained propellant
        self.assertLess(sim.m, sim.rocket.total_mass())
    def test_abort_capsule_lands_safely(self):
        sim = _ascent(); sim.cfg.dt_mode = "auto"
        while sim.met < 40 and not sim.terminal(): sim.step()
        sim.abort(); self.assertTrue(sim.capsule)
        for _ in range(200000):
            if sim.terminal(): break
            sim.step()
        self.assertEqual(sim.status, "LANDED"); self.assertTrue(sim.chute_open)
    def test_stage_debris_falls_back(self):
        sim = _ascent(); last = len(sim.plan) - 1
        while sim.phase_idx < 3 and not sim.terminal(): sim.step()
        self.assertTrue(any(d["kind"] == "stage" for d in sim.debris))
        n_alive = lambda: sum(d["alive"] for d in sim.debris)
        sim.cfg.failures = False
        while sim.met < 1500 and n_alive() > 0 and sim.status == "FLYING": sim.step()
        self.assertTrue(any("impact" in m for _, m in sim.events))


class TestOrbitTools(unittest.TestCase):
    def _leo(self):      # equatorial start: the starting point is a node, so a normal burn is a pure plane change
        return Simulation(launch=LaunchConfig(start_mode="orbit", orbit_altitude_m=400e3, lat_deg=0.0, lon_deg=0.0), config=SimConfig(dt_mode="auto"))
    def test_prograde_burn_matches_hohmann_apoapsis(self):
        sim = self._leo(); mu = sim.gm[sim.li]; r1 = sim.radii[sim.li] + 400e3; r2 = r1 + 600e3
        dv = orbital.hohmann(mu, r1, r2)["dv1"]; out = sim.maneuver_preview(dv_pro=dv)
        self.assertAlmostEqual(out["after"]["apo_alt"], 1000e3, delta=500.0); self.assertAlmostEqual(out["after"]["peri_alt"], 400e3, delta=500.0)
    def test_normal_burn_changes_inclination_only(self):
        sim = self._leo(); v = math.sqrt(sim.gm[sim.li] / (sim.radii[sim.li] + 400e3)); out = sim.maneuver_preview(dv_norm=v * math.tan(math.radians(5)))
        self.assertAlmostEqual(out["after"]["inc"] - out["before"]["inc"], 5.0, delta=0.05)
    def test_predict_returns_closed_orbit_without_touching_sim(self):
        sim = self._leo(); t0 = sim.t; r0 = sim.rp.copy(); T = 2 * math.pi * math.sqrt((sim.radii[sim.li] + 400e3) ** 3 / sim.gm[sim.li])
        pts, body = sim.predict(T, 120); self.assertEqual(body, "Earth"); self.assertEqual(sim.t, t0); self.assertTrue((sim.rp == r0).all())
        self.assertLess(np.linalg.norm(pts[-1] - pts[0]), 20e3)                                    # returns near start after one period
    def test_apply_impulse_changes_orbit(self):
        sim = self._leo(); a0 = sim.telemetry()["sma_m"]; sim.apply_impulse(dv_pro=100.0); self.assertGreater(sim.telemetry()["sma_m"], a0 + 1e5)
    def test_orbit_log_recorded_on_events(self):
        sim = _ascent(); last = len(sim.plan) - 1
        while sim.phase_idx < last and not sim.terminal(): sim.step()
        self.assertGreater(len(sim.orbit_log), 4); self.assertTrue(any("separation" in e["label"] for e in sim.orbit_log))


class TestLambertAndTransfers(unittest.TestCase):
    def test_lambert_curtis_example(self):      # Curtis, Orbital Mechanics for Engineering Students, Example 5.2
        v1, v2 = lam.lambert([5000.0, 10000.0, 2100.0], [-14600.0, 2500.0, 7000.0], 3600.0, 398600.0)
        np.testing.assert_allclose(v1, [-5.9925, 1.9254, 3.2456], atol=2e-3); np.testing.assert_allclose(v2, [-3.3125, -4.1966, -0.3853], atol=2e-3)
    def test_lambert_solution_propagates_to_target(self):
        mu = 398600.0; r1 = np.array([7000.0, 0, 0]); r2 = np.array([0, 12000.0, 1500.0]); tof = 2500.0; v1, v2 = lam.lambert(r1, r2, tof, mu)
        f = lambda t, y: np.concatenate([y[3:], -mu * y[:3] / np.linalg.norm(y[:3]) ** 3]); y = np.concatenate([r1, v1]); t = 0.0
        while t < tof - 1e-9: y = integ.rk4(f, t, y, 1.0); t += 1.0
        self.assertLess(np.linalg.norm(y[:3] - r2), 1e-4)
    def test_synodic_period_earth_mars(self):
        self.assertAlmostEqual(transfer.synodic_period_days(SolarSystem(), "Earth", "Mars"), 779.9, delta=1.0)
    def test_porkchop_finds_known_mars_window(self):      # real 2001 Mars Odyssey: launched ~day 462 after J2000, ~200 d flight, C3 ~ 12 km2/s2
        pc = transfer.porkchop(SolarSystem(), "Earth", "Mars", 0, 800, 120, 350, 30, 30); b = pc["best"]
        self.assertTrue(440 < b["dep_day"] < 500); self.assertTrue(170 < b["tof_days"] < 230); self.assertTrue(3000 < b["vinf_dep"] < 4000)
    def test_start_day_moves_planets(self):
        a = Simulation(); b = Simulation(launch=LaunchConfig(start_day=100.0)); ie = a.names.index("Earth")
        ang = math.acos(np.dot(a.bp[ie] - a.bp[0], b.bp[ie] - b.bp[0]) / np.linalg.norm(a.bp[ie] - a.bp[0]) / np.linalg.norm(b.bp[ie] - b.bp[0]))
        r0, _ = transfer.body_state(a.system, "Earth", 0.0); r1, _ = transfer.body_state(a.system, "Earth", 100 * 86400.0)        # Kepler reference (true anomaly advances unevenly: e = 0.0167)
        expect = math.acos(np.dot(r0, r1) / np.linalg.norm(r0) / np.linalg.norm(r1))
        self.assertAlmostEqual(math.degrees(ang), math.degrees(expect), delta=0.3); self.assertAlmostEqual(b.t, 100 * 86400)
    def test_transfer_start_preserves_v_infinity(self):
        s = SolarSystem(); L, t = transfer.to_launch_config(s, "Earth", "Mars", 469.0, 199.0); sim = Simulation(system=s, launch=L)
        ie = sim.names.index("Earth"); eps = 0.5 * np.linalg.norm(sim.rv - sim.bv[ie]) ** 2 - sim.gm[ie] / np.linalg.norm(sim.rp - sim.bp[ie])
        self.assertAlmostEqual(math.sqrt(2 * eps), t["vinf_dep"], delta=1.0)
    def test_lambert_transfer_flies_near_mars(self):
        s = SolarSystem(); pc = transfer.porkchop(s, "Earth", "Mars", 0, 800, 120, 350, 30, 30); b = pc["best"]; L, t = transfer.to_launch_config(s, "Earth", "Mars", b["dep_day"], b["tof_days"])
        sim = Simulation(system=s, launch=L, plan=[Phase("coast", "coast", 0.0)], config=SimConfig(dt_mode="auto")); im = sim.names.index("Mars"); best = 1e30
        while sim.met < b["tof_days"] * 86400 * 1.1 and not sim.terminal(): sim.step(); best = min(best, float(np.linalg.norm(sim.rp - sim.bp[im])))
        self.assertLess(best, 5e9)          # within 0.03 AU: N-body + mean-element differences leave a mid-course correction to do


class TestReentryLandingGroundTrack(unittest.TestCase):
    def test_allen_eggers_peak_deceleration(self):
        import copy
        m = copy.deepcopy(SolarSystem().get("Mars")); m.radius_m *= 50; m.gm *= 1e-3; H = m.atmosphere.scale_height_m      # flat, gravity-free: Allen-Eggers assumptions
        for v, g in ((5800.0, 15.0), (7000.0, 8.0)):
            r = reentry.entry(m, 1000.0, 1.5, 3.0, 0.5, v, g, dt=0.02); ae = v ** 2 * math.sin(math.radians(g)) / (2 * math.e * H) / 9.80665
            self.assertAlmostEqual(r.peak_decel_g / ae, 1.0, delta=0.02)
    def test_earth_leo_entry_is_plausible(self):
        r = reentry.entry(SolarSystem().get("Earth"), 5000.0, 1.3, 12.0, 4.7, 7800.0, 2.0); self.assertTrue(r.reached_surface); self.assertTrue(4 < r.peak_decel_g < 12)
    def test_hover_start_free_fall_time(self):
        L, plan = moon_descent(1000.0); sim = Simulation(rocket=rocket_library.lunar_lander(), launch=L, plan=[Phase("coast", "coast", 0.0)], config=SimConfig(dt_mode="auto", failures=False))
        while not sim.terminal() and sim.met < 100: sim.step()
        self.assertAlmostEqual(sim.met, math.sqrt(2 * 1000.0 / (sim.gm[sim.li] / sim.radii[sim.li] ** 2)), delta=2.0)
    def test_powered_landing_is_soft(self):
        r = challenges.moon_landing(); self.assertTrue(r.passed, r.message); self.assertGreater(r.sim.telemetry()["propellant_kg"], 3000)
    def test_ground_track_at_pad_matches_launch_site(self):
        tm = Simulation().telemetry(); self.assertAlmostEqual(tm["latitude_deg"], 28.5, delta=0.01); self.assertAlmostEqual(tm["longitude_deg"], -80.6, delta=0.01)
    def test_equatorial_launch_stays_on_equator_band(self):
        L, plan = earth_leo(200e3, 6.0); L.lat_deg = 0.0; sim = Simulation(launch=L, plan=plan, config=SimConfig(dt_mode="auto"))
        while sim.met < 300 and not sim.terminal(): sim.step()
        self.assertLess(abs(sim.telemetry()["latitude_deg"]), 3.0)


class TestLibraryStudiesChallenges(unittest.TestCase):
    def test_every_library_rocket_is_valid_and_builds(self):
        for name, fn in rocket_library.LIBRARY.items():
            r = fn(); e = r.estimates(); self.assertGreater(e["delta_v_mps"], 0, name); self.assertEqual([w for w in r.validate() if "cannot lift off" in w], [], name)
            self.assertGreater(len(build_rocket_parts(r)), 4, name)
    def test_sounding_rocket_does_not_reach_orbit_and_ssto_fails(self):
        self.assertNotEqual(run_survival_test(rocket_library.sounding_rocket()).verdict, "SURVIVED"); self.assertNotEqual(run_survival_test(rocket_library.ssto_attempt()).verdict, "SURVIVED")
    def test_param_paths(self):
        r = default_rocket(); self.assertEqual(studies.get_param(r, "stages[0].engine.count"), 9); studies.set_param(r, "stages[1].dry_mass_kg", 5000.0); self.assertEqual(r.stages[1].dry_mass_kg, 5000.0)
        studies.set_param(r, "limits.max_q_pa", 1234.0); self.assertEqual(r.limits.max_q_pa, 1234.0)
    def test_sweep_payload_trend(self):
        rows = studies.sweep(default_rocket(), "payload_mass_kg", [2000.0, 10000.0, 60000.0]); self.assertTrue(rows[0]["survived"]); self.assertFalse(rows[-1]["survived"])
    def test_monte_carlo_reproducible(self):
        a = studies.monte_carlo(default_rocket(), n=3, seed=5); b = studies.monte_carlo(default_rocket(), n=3, seed=5); self.assertEqual(a["verdicts"], b["verdicts"]); self.assertTrue(0.0 <= a["success_rate"] <= 1.0)
    def test_challenges(self):
        self.assertTrue(challenges.first_orbit().passed); self.assertTrue(challenges.gentle_ascent().passed)


class TestGpuSelection(unittest.TestCase):
    def test_classify_gpu_names(self):
        self.assertEqual(gpu.classify("NVIDIA GeForce RTX 3050 Laptop GPU"), "discrete"); self.assertEqual(gpu.classify("AMD Radeon RX 6600"), "discrete")
        self.assertEqual(gpu.classify("Intel(R) UHD Graphics 620"), "integrated"); self.assertEqual(gpu.classify("AMD Radeon(TM) Graphics"), "integrated")
        self.assertEqual(gpu.classify("Microsoft Basic Render Driver"), "software"); self.assertEqual(gpu.classify("llvmpipe (LLVM 15.0.7, 256 bits)"), "software")
    def test_backend_choice(self):
        hw = [dict(name="x", kind="integrated")]; sw = [dict(name="y", kind="software")]
        self.assertEqual(gpu.choose_backend("auto", hw), "gpu"); self.assertEqual(gpu.choose_backend("auto", sw), "cpu"); self.assertEqual(gpu.choose_backend("auto", []), "gpu")
        self.assertEqual(gpu.choose_backend("cpu", hw), "cpu"); self.assertEqual(gpu.choose_backend("gpu", sw), "gpu")
    def test_lspci_parsing_dual_gpu_laptop(self):
        out = gpu.parse_lspci("00:02.0 VGA compatible controller: Intel Corporation UHD Graphics 620\n01:00.0 3D controller: NVIDIA Corporation GP107M [GeForce GTX 1050 Mobile]\n00:1f.3 Audio device: Intel")
        self.assertEqual([g["kind"] for g in out], ["integrated", "discrete"])
    def test_software_renderer_detection(self):
        self.assertTrue(gpu.is_software_renderer("GDI Generic")); self.assertFalse(gpu.is_software_renderer("NVIDIA GeForce GTX 1650/PCIe/SSE2"))


if __name__ == "__main__":
    unittest.main()
