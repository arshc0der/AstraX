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
        sim = Simulation(launch=LaunchConfig(start_mode="orbit", orbit_altitude_m=100e3), config=SimConfig(dt_mode="auto"))
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


if __name__ == "__main__":
    unittest.main()
