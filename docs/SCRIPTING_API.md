# Scripting API

AstraX has two scripting levels: the in-app **flight computer** and the **Python engine API**.

## 1. In-app flight computer (Mission control ▸ Flight computer)
Define `mission_loop()`; it runs every physics step while *Enable script control* is on and overrides the flight plan.

```python
def mission_loop():
    alt = rocket.get_altitude()          # km above the dominant body
    v   = rocket.get_velocity()          # m/s relative to the dominant body
    if alt < 10:
        rocket.set_pitch(90); rocket.set_thrust(1.0)
    elif alt < 100:
        rocket.set_pitch(60); rocket.set_thrust(1.0)
    elif v < 7600:
        rocket.set_pitch(0); rocket.set_thrust(1.0)
    else:
        rocket.set_thrust(0.0)
```
| Function | Meaning |
|---|---|
| `rocket.set_thrust(x)` | throttle 0–1 |
| `rocket.set_pitch(deg)` | 90 = straight up, 0 = horizontal (local horizon frame) |
| `rocket.set_heading(deg)` | 0 = north, 90 = east |
| `rocket.get_altitude()` | km |
| `rocket.get_velocity()` / `get_surface_velocity()` | m/s |
| `rocket.get_fuel()` | kg remaining |
| `rocket.get_apoapsis()` / `get_periapsis()` | km altitude |
| `rocket.stage()` | separate the next stage |
| `rocket.log(text)` | write to the event log |

`math` is available; builtins are restricted (no `import`, `open`, `exec`). **This is not a security sandbox** - run only scripts you trust.

## 2. Engine API (no GUI)
```python
from astrax.simulation import Simulation, LaunchConfig, SimConfig, Phase
from astrax.rocket_library import get_rocket
from astrax.missions import earth_leo

L, plan = earth_leo(target_alt_m=200e3, kick_deg=6.0)
sim = Simulation(rocket=get_rocket("Falcon-class 2-stage (default)"), launch=L, plan=plan, config=SimConfig(dt_mode="auto"))
while not sim.terminal() and sim.phase_idx < len(plan) - 1:
    sim.step()
tm = sim.telemetry()                       # dict of ~60 values (SI units)
print(sim.status, tm["periapsis_alt_m"] / 1e3, "km")
```

### Common tasks
```python
# survival test of any design
from astrax.survival import run_survival_test
r = run_survival_test(my_rocket); print(r.verdict, r.headline)

# launch window search + start a simulation on the transfer
from astrax import transfer
from astrax.bodies import SolarSystem
s = SolarSystem(); best = transfer.porkchop(s, "Earth", "Mars", 0, 800, 120, 350)["best"]
L, info = transfer.to_launch_config(s, "Earth", "Mars", best["dep_day"], best["tof_days"])

# re-entry
from astrax import reentry
res = reentry.entry(s.get("Earth"), 5000, 1.3, 12.0, 4.7, 7800, 2.0); print(res.peak_decel_g)

# what-if orbit change on a running simulation
print(sim.maneuver_preview(dv_pro=100)["after"]["apo_alt"]); pts, body = sim.predict(5400)

# emergencies from code
sim.emergency("engine_out"); sim.emergency("fuel_leak", 300.0); sim.abort()

# studies
from astrax import studies
rows = studies.sweep(my_rocket, "payload_mass_kg", [2000, 6000, 10000])
mc = studies.monte_carlo(my_rocket, n=20, seed=1)
```

### Recording and export
```python
from astrax.recorder import Recorder, save_report
rec = Recorder(interval_s=1.0)
while ...: sim.step(); rec.maybe_record(sim)
rec.export_csv("run.csv"); rec.save_session("run.json"); save_report("report.md", sim, rec, my_rocket.estimates())
```
Full signatures: [API_REFERENCE](API_REFERENCE.md). Conventions: SI units everywhere (m, kg, s, N, Pa, J) except where a name says `_km`, `_deg`, `_days`.
