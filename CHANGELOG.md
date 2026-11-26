# Changelog

All notable changes to this project are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/); versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]
- _nothing yet_

## 4.0.0 - 2026-11-21
**"Foundation": professional repository release. No change to simulation or UI behaviour compared with 3.2.1.**
### Added
- Professional `README.md` (badges, gallery, features, validation table, architecture diagram, citation).
- Documentation for users, testers and developers: INSTALLATION, KEYBOARD_SHORTCUTS, GLOSSARY, TROUBLESHOOTING, EDUCATORS; tester hub with 140 generated manual test cases (+CSV), smoke test, regression checklist, exploratory charters, performance/compatibility/test-data/known-issues/release docs; developer hub with coding standards, adding-physics guide, debugging, CI/CD, packaging, release process, documentation guide and ADR log.
- Community files: CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, GOVERNANCE, MAINTAINERS, ROADMAP, AUTHORS, THIRD_PARTY_NOTICES, CITATION.cff.
- GitHub setup: issue forms (bug, feature, test report, docs), PR template, CODEOWNERS, Dependabot, labeler, stale bot, CodeQL, CI (lint, tests on 3 OS x 3 Python, UI import smoke, docs checks) and a release workflow (PyInstaller builds, checksums, notes).
- `pyproject.toml`, `Makefile`, `.editorconfig`, `.gitattributes`, `.pre-commit-config.yaml`, `MANIFEST.in`.
- Tools: `--diagnostics` flag, `tools/benchmark.py`, `check_docs_links.py`, `check_screenshots.py`, `gen_test_cases.py`, `release_notes.py`, `set_repo_slug.py`.
- Screenshot placeholders (`docs/screenshots/`), social preview image and banner.
- Repository health tests (`tests/test_repo_health.py`).
### Changed
- Version 4.0.0; documentation index reorganised by audience.

## 3.2.1-dev
* **GPU/CPU selection:** detect GPUs; Auto/GPU/CPU rendering; prefer high-performance GPU (Windows registry preference, Linux PRIME); `--gpu-info`, `--gpu`, `--cpu`; status-bar renderer display; hint when a GPU exists but the CPU renders.
* **Lag fixes:** snapshot back-pressure, one-time orbit-line upload, ring-buffer trail, visible-tab-only graph redraws, shorter physics slices, GIL switch interval, Performance quality mode, refresh-rate cap, `UI ms` indicator.
* New doc: GRAPHICS_AND_PERFORMANCE.

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
