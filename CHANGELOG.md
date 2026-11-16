# Changelog
## 3.0.0-dev
* New `astrax/` headless engine (N-body, RK4/DOPRI5/Verlet, variable mass, atmosphere+drag, staging, flight plans, recorder, reports) - 30 tests.
* New PyQt6 UI: dockable workspaces, rocket designer with procedural 3D rocket, planet inspector, mission control, telemetry/analysis, education, GIF/MP4 recording, logging.
* Original `core/` (Euler planets, simple physics) moved to `legacy/core/` for reference; the original `mission_loop()` script API is preserved in `astrax/runtime.py`.
