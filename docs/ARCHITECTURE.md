# Architecture

```
main.py                       entry: Qt app, theme, splash, preload thread, MainWindow
astrax/   (engine, NO Qt/OpenGL imports - testable headless)
  constants.py  bodies.py  orbital.py  integrators.py  atmosphere.py
  aero.py  structure.py                    aerodynamics, heating, skin stress, limits
  rocket.py  rocket_mesh.py  rocket_library.py
  simulation.py                            the physics engine (state, forces, guidance, staging, failures, debris)
  missions.py  survival.py  studies.py  challenges.py
  lambert.py  transfer.py  reentry.py      interplanetary + entry tools
  recorder.py  project.py  runtime.py      telemetry/export, save/load, user scripts
ui/       (PyQt6 / pyqtgraph / PyOpenGL)
  main_window.py  sim_worker.py            window + background simulation thread
  viewport.py  rocket_designer.py  planet_inspector.py  mission_panel.py
  telemetry.py  orbit_panel.py  emergency_panel.py  planner_panel.py  studies_panel.py  challenges_panel.py
  survival_dialog.py  extra_windows.py  settings_dialog.py  education.py
  theme.py  winframe.py  splash.py  video.py  worker_util.py
assets/   logo, icons, splash frames, branding SVG originals      tools/  build_branding.py  gen_docs.py
tests/    test_physics.py (65 tests)                              docs/   this documentation
```

## Layering rules
1. `astrax/` never imports Qt. UI code never contains physics.
2. The **simulation runs on its own thread** (`SimWorker`). The UI sends commands through a queue (`worker.command(...)`) and receives immutable **snapshots** via a signal, so there are no data races.
3. Heavy studies (survival test, porkchop, Monte Carlo) run in `FuncWorker` threads and never touch the live simulation (they build their own `Simulation`).

## Simulation core (astrax/simulation.py)
- **State** `y = [body positions, body velocities, rocket position, rocket velocity, rocket mass]`, barycentric ecliptic J2000.
- **Step**: guidance (phase → direction + throttle) → autopilot protection (g, max-Q) → faults → stage flows → integrate (RK4 / DOPRI5 / Verlet) with exact linear mass change → propellant bookkeeping → post-step (loads/failures, staging, contact, debris).
- **Forces**: N-body gravity, thrust (pressure-dependent Isp), drag Cd(Mach), normal force (angle of attack), parachute.
- **Time step**: `auto_dt()` = min of orbital (0.02 rad), scale-height, drag-relaxation, ground-approach and burn limits.
- **Terminal states**: `LANDED`, `CRASHED`, `DESTROYED` (after `post_failure_s`). `terminal()` is the single test.

## Data flow in the UI
`SimWorker` loop: drain commands → advance (with wall-clock budget; never coarsens physics) → record telemetry → build snapshot → `snapshot` signal → `MainWindow.on_snapshot` fans out to viewport, telemetry, emergency, orbit panels and extra windows.

## Start-up sequence
`main.py`: create app → apply theme/palette/stylesheet → install title-bar frame filter → show animated splash → preload heavy modules on a thread (splash keeps animating) → build `MainWindow` → `splash.finish(window)` (waits for the 3.8 s intro, fades out).
