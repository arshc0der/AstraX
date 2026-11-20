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


if __name__ == "__main__":
    unittest.main()
