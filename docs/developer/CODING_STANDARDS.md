# Coding standards

## Principles
1. **Correctness and honesty first** - never present unvalidated results as research-grade.
2. **Separation:** `astrax/` (engine) never imports Qt/OpenGL; `ui/` never contains physics.
3. **Readable over clever.** The existing code is compact (several statements per line); new code may be more spacious - match the surrounding file, prefer clarity.
4. **Everything testable** without a display.

## Python
- Python 3.10+ syntax; `from __future__ import annotations` in engine modules.
- Type hints on public functions where practical; dataclasses for data.
- Docstrings (first line = summary) on every public class/function - they feed `docs/API_REFERENCE.md`.
- No broad `except:`; catch specific exceptions; never swallow errors silently in the engine (UI may show a message).
- No global mutable state in `astrax/` (the `Simulation` object owns its state).
- Dependencies: standard library + the five runtime packages. A new dependency needs an issue and maintainer approval.

## Units and naming
- **SI internally**: m, kg, s, N, Pa, J, rad where not stated.
- Put the unit in the name: `altitude_m`, `mass_kg`, `thrust_n`, `period_s`, `inc_deg`, `dv_mps`, `dist_target_m`.
- Angles in degrees only at the UI/preset boundary (`*_deg`); radians in maths.
- Frames: barycentric ecliptic J2000 inertial unless a name says otherwise (`rel_*` = relative to the dominant body).

## Physics code
- State assumptions in the docstring; cite equations/sources; list limitations in `docs/PHYSICS.md`.
- Add **a test against an analytic or published value** (see [ADDING_PHYSICS](ADDING_PHYSICS.md)).
- Keep integrator math vectorised with NumPy; avoid per-step allocations in hot loops where easy.
- Do not change default numerical tolerances silently.

## Qt / UI rules
- All long work off the GUI thread (`FuncWorker`, `SimWorker.command`).
- Never read data another thread mutates without a lock/copy (`Recorder.arrays`).
- Do **not** override Qt method names (`update`, `move`, `result`, `close`, `show`...): use `update_snapshot`, `move_stage`, `outcome`.
- Never create/destroy GL items inside `paintGL`; defer with `QTimer.singleShot(0, ...)`.
- `QAction(None, ...)` is invalid in PyQt6 - use the correct overload.
- Enums use the full PyQt6 path: `Qt.AlignmentFlag.AlignTop`.
- Wrap large panels in `QScrollArea` so they cannot force a huge minimum window size.
- Every control gets a tooltip; every number shows its unit.
- Colours come from the theme (`ui/theme.py`), never hard-coded in widgets (graph accents excepted).

## Files and formats
JSON with an `astrax_format` tag; new fields need defaults; document in `tools/gen_docs.py` data.

## Tests
`unittest`, headless, deterministic (seeded RNG), with explicit tolerances. Slow tests (> 20 s) need a comment. Tests must not need network or a display.

## Commits and PRs
Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `ci:`, `chore:`). One logical change per PR. Update `CHANGELOG.md` (Unreleased).

## Review checklist
Correct? Tested? Units clear? Layering respected? Threads safe? Docs updated? Backwards compatible? Performance impact? Screenshots for UI?
