# Testing guide (strategy)

## Test pyramid in AstraX
| Layer | What | Where | Run by |
|---|---|---|---|
| **Unit / numerical** | orbits, integrators, atmosphere, rocket equation, Lambert, re-entry | `tests/test_physics.py` | CI on every push (3 OS × 3 Python) |
| **Integration** | full ascent to orbit, survival test, abort landing, Moon landing, Mars transfer flight, scenario/session round-trips | `tests/test_physics.py` | CI |
| **Repository health** | links, version consistency, required files, screenshots map | `tests/test_repo_health.py` | CI |
| **UI import smoke** | every UI module imports and `MainWindow` constructs (offscreen Qt) | CI job `ui-import-smoke` | CI |
| **Manual / exploratory** | real windows, real GPUs, usability, visuals | `docs/tester/` | testers before releases |
| **Performance** | steps/s, UI frame time | `tools/benchmark.py`, status bar | testers / maintainers |

> The physics engine is extensively unit-tested. **The GUI relies mainly on manual testing** because 3D/GPU behaviour cannot be fully automated. That is why tester contributions matter.

## What is validated against what
| Area | Reference |
|---|---|
| Orbit math | closed-form Kepler, Hohmann tables |
| Integrators | analytic oscillator (order of convergence), energy conservation |
| Rocket equation | Tsiolkovsky |
| Lambert | Curtis Example 5.2, propagation consistency |
| Launch windows | the real 2001 Mars Odyssey window, synodic period |
| Re-entry | Allen–Eggers |
| Atmosphere | US Standard Atmosphere 1976 table |
See [../VALIDATION.md](../VALIDATION.md) for every automated test.

## Test levels for a change
| Change | Minimum testing |
|---|---|
| Doc typo | link check |
| UI cosmetic | smoke test + the affected area's P1/P2 cases |
| New UI feature | new manual cases added to `tools/gen_test_cases.py` + exploratory session |
| Physics model | unit test vs analytic value + integration test + regression checklist |
| Performance change | benchmark before/after + UI ms on the 3 reference scenarios |
| Release | full regression checklist on ≥ 2 OS + smoke on all supported OS |

## Defect lifecycle
`New` → `Triaged` (severity/priority, labels) → `Confirmed` (reproduced) → `In progress` → `Fixed` (PR linked) → `Verified` (tester re-runs steps on the fixed build) → `Closed`. Not reproducible → `needs-info`; auto-closed after 14 days without reply.

## Test data
Reusable scenarios and expected values: [TEST_DATA.md](TEST_DATA.md). Share failing inputs as JSON (rocket/scenario/session files).

## Automation wish-list (contributions welcome)
- Qt Test / pytest-qt tests for panels with an offscreen platform.
- Screenshot regression with a software OpenGL renderer.
- Headless scenario runner (`astrax-run`) for batch regression.
