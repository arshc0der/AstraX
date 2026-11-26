"""Headless performance benchmark of the engine.   python tools/benchmark.py   (writes benchmark.json)"""
import json, os, platform, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def timed(fn):
    t = time.perf_counter(); r = fn(); return time.perf_counter() - t, r


def main():
    from astrax.simulation import Simulation, SimConfig, LaunchConfig
    from astrax.missions import earth_leo
    from astrax.survival import run_survival_test
    from astrax.rocket import default_rocket
    from astrax.bodies import SolarSystem
    from astrax import transfer
    out = {"python": sys.version.split()[0], "platform": platform.platform(), "results": {}}

    def ascent():
        L, plan = earth_leo(); s = Simulation(launch=L, plan=plan, config=SimConfig(dt_mode="auto"))
        while s.met < 1500 and not s.terminal() and s.phase_idx < len(plan) - 1: s.step()
        return s.steps
    t, steps = timed(ascent); out["results"]["Full ascent to orbit"] = dict(seconds=round(t, 2), steps=steps, steps_per_s=round(steps / t))
    def coast():
        s = Simulation(launch=LaunchConfig(start_mode="orbit"), config=SimConfig(dt_s=600, method="rk4")); s.advance(86400 * 30); return s.steps
    t, steps = timed(coast); out["results"]["30-day N-body coast (dt 600 s)"] = dict(seconds=round(t, 2), steps=steps, steps_per_s=round(steps / t))
    t, r = timed(lambda: run_survival_test(default_rocket())); out["results"]["Survival test (demo rocket)"] = dict(seconds=round(t, 2), verdict=r.verdict)
    t, _ = timed(lambda: transfer.porkchop(SolarSystem(), "Earth", "Mars", 0, 800, 120, 350, 30, 30)); out["results"]["Porkchop 30x30 Earth-Mars"] = dict(seconds=round(t, 2))
    w = max(len(k) for k in out["results"]); print(f"Python {out['python']} on {out['platform']}")
    for k, v in out["results"].items(): print(f"  {k:<{w}}  " + "  ".join(f"{a}={b}" for a, b in v.items()))
    json.dump(out, open("benchmark.json", "w"), indent=2)


if __name__ == "__main__":
    main()
