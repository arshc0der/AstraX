# Changelog
## 3.2.0-dev
* **Branding:** new logo, animated SVG splash (pre-rendered, theme-coloured), window/taskbar icons, About dialog; dark Fusion palette and themed native title bar on Windows; dark theme default; `tools/build_branding.py`.
* **Interplanetary:** Lambert solver, launch-window porkchop planner, N-body flight of the transfer, start epoch (`start_day`), `transfer` start mode.
* **Landing & entry:** powered-landing guidance, `hover` start, lunar lander, re-entry calculator (Allen-Eggers validated).
* **Research tools:** parameter sweeps, maximum payload, Monte Carlo, challenges, ground track, example rocket library.
* **Fixes:** normal force when flying backwards, auto time-step uses air-relative speed and ground-approach time, capsule loads telemetry, thread-safe recorder.
* **Docs:** full documentation set (quick start, tutorials, UI reference, scripting API, architecture, developer guide, FAQ, branding) plus generated API/file-format/validation references. Tests: 46 -> 65.
## 3.1.0-dev
* Aerodynamics: Mach-dependent drag, angle-of-attack normal force, Sutton-Graves heating, speed of sound.
* Structure & survival: materials, wall thickness, design limits, failure model (overload, overheating, yield, loss of control), autopilot load protection, **survival test** with verdict, margins and 3D replay.
* Emergencies: abort with parachute capsule, engine-out, propellant leak, stuck throttle, guidance loss.
* Animation: engine plume, launch pad, launch camera, jettisoned-stage debris, explosion and fragments, on-screen banners.
* Orbit analysis: orbit log per event, maneuver planner (preview / predicted path / impulse), Hohmann helper.
* Windows & customisation: extra 3D views and graph windows, themes, font size, settings dialog.
* Tests: 30 -> 46.
## 3.0.0-dev
* New `astrax/` headless engine (N-body, RK4/DOPRI5/Verlet, variable mass, atmosphere+drag, staging, flight plans, recorder, reports) - 30 tests.
* New PyQt6 UI: dockable workspaces, rocket designer with procedural 3D rocket, planet inspector, mission control, telemetry/analysis, education, GIF/MP4 recording, logging.
* Original `core/` (Euler planets, simple physics) moved to `legacy/core/` for reference; the original `mission_loop()` script API is preserved in `astrax/runtime.py`.
