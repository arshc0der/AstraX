# Debugging guide

## Quick diagnostics
`python main.py --diagnostics` · `--gpu-info` · logs in `logs/astrax_*.log` (includes the OpenGL renderer line) · status bar `UI xx ms`, `GPU:`/`CPU rendering:`.

## Reproduce without the GUI
```python
from astrax.simulation import Simulation, SimConfig
from astrax.missions import earth_leo
L, plan = earth_leo(); sim = Simulation(launch=L, plan=plan, config=SimConfig(dt_mode="auto"))
while not sim.terminal() and sim.phase_idx < len(plan) - 1: sim.step()
print(sim.status, sim.events[-5:], sim.telemetry())
```
Every simulation question can be asked this way; add a unit test from the repro.

## Common problems
| Symptom | Likely cause | Where to look |
|---|---|---|
| `X and Y arrays must be the same shape` | reading recorder lists while the sim thread appends | use `Recorder.arrays(...)` |
| Huge memory allocation at start | `GLGridItem.setSize` before `setSpacing` | `ui/viewport.py` |
| `TypeError: QAction(...)` | `None` icon argument | `MainWindow._act` |
| Window demands a giant size | panel without `QScrollArea` | `MainWindow._scroll` |
| Orbit wrong after long step | dt too large / wrong integrator | `Simulation.stability_warnings`, `auto_dt` |
| Capsule never lands / crashes | drag stiffness; use air-relative speed in `auto_dt` | `auto_dt` |
| Rocket flies sideways after abort | backward-flight normal force sign | `aero.normal_force` |
| GL items vanish/crash | rebuilt inside `paintGL` | defer with `QTimer.singleShot(0, ...)` |
| UI freezes | physics/long work on the GUI thread | `SimWorker`, `FuncWorker` |
| Lag grows over time | frames queue up | back-pressure (`SimWorker.ack`) |

## Qt debugging
- Verbose Qt logging: `QT_LOGGING_RULES="qt.*=true"`; platform plugin issues: `QT_DEBUG_PLUGINS=1`.
- OpenGL backend: `QT_OPENGL=software|desktop`; platform: `QT_QPA_PLATFORM=offscreen` (headless), `xcb` (Linux).
- Python faulthandler: `python -X faulthandler main.py` prints native crash tracebacks.

## Profiling
```bash
python -m cProfile -o prof.out tools/benchmark.py
python -c "import pstats; pstats.Stats('prof.out').sort_stats('cumtime').print_stats(25)"
```
GUI frame time is in the status bar (`UI ms`). For per-function GUI profiling run the app under `cProfile` and exercise the slow path.

## Numerical debugging checklist
1. Energy / angular momentum conserved in a gravity-only run?
2. Does halving dt change the answer? (convergence)
3. Is the frame right (inertial vs body-fixed; air-relative vs inertial speed)?
4. Units: any `_km` mixed with `_m`?
5. Is a guidance/throttle decision made once per step (zero-order hold)?

## Stub-Qt trick
For logic bugs in UI code without a display, import `ui.*` against stub Qt classes and call handlers with synthetic snapshots (see git history / `CONTRIBUTING.md`); real rendering still needs a real run.
