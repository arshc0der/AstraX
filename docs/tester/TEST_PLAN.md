# Test plan - AstraX 4.0

## 1. Scope
**In scope:** the desktop application (Windows, Linux, macOS), the engine package `astrax/`, file formats, documentation accuracy, install procedures, graphics (GPU/CPU), performance.
**Out of scope:** real-world mission accuracy (models are simplified), third-party library defects (reported upstream), non-supported Python versions.

## 2. Objectives
1. No crashes or hangs in normal use.
2. All documented features work as described.
3. Physics results match the validation references.
4. Acceptable performance on mainstream hardware.
5. Installation works on a clean machine following the docs.

## 3. Test items
Engine (`astrax/`), UI (`ui/`), tools (`tools/`), assets (logo/splash), docs, packaging (PyInstaller builds), CI workflows.

## 4. Approach
Automated unit/integration/health tests (CI) + manual suite ([MANUAL_TEST_CASES](MANUAL_TEST_CASES.md)) + exploratory charters ([EXPLORATORY_CHARTERS](EXPLORATORY_CHARTERS.md)) + performance checks ([PERFORMANCE_TESTING](PERFORMANCE_TESTING.md)) + compatibility ([COMPATIBILITY_MATRIX](COMPATIBILITY_MATRIX.md)).

## 5. Environments
| ID | OS | Python | GPU | Notes |
|---|---|---|---|---|
| E1 | Windows 11 | 3.12 | NVIDIA discrete + Intel iGPU (laptop) | primary; check GPU preference |
| E2 | Windows 10 | 3.10 | Intel iGPU only | minimum spec |
| E3 | Ubuntu 24.04 | 3.12 | Intel/AMD Mesa | Wayland + X11 |
| E4 | Fedora/Arch | latest | NVIDIA proprietary | driver variants |
| E5 | macOS (Apple Silicon) | 3.12 | Apple GPU | OpenGL via Metal translation |
| E6 | any | any | forced `--cpu` | software rendering |
| E7 | VM (VirtualBox/VMware) | any | virtual GPU | worst-case graphics |

## 6. Entry criteria
Build installs; CI green on `main`; changelog updated; screenshots present.
## 7. Exit criteria (release)
- 100 % of P1 manual cases pass on E1, E3 and one of E2/E5.
- ≥ 95 % of P2 cases pass; no open Crash/Data-loss defects; no open P1 failures.
- Automated tests pass on all CI matrix cells.
- Smoke test passes on every supported OS.
- Known issues documented in [KNOWN_ISSUES](KNOWN_ISSUES.md).

## 8. Severity and priority
| Severity | Definition | Example |
|---|---|---|
| S1 Critical | crash, data loss, cannot start | traceback at startup |
| S2 Major | feature unusable, wrong physics result | survival test never returns |
| S3 Minor | workaround exists, visual glitch | label overlap |
| S4 Trivial | cosmetic/typo | wrong tooltip |

Priority: P1 fix before release · P2 next release · P3 backlog.

## 9. Deliverables
Test report issues per environment, defect issues, updated regression results, release checklist sign-off.

## 10. Risks
| Risk | Mitigation |
|---|---|
| GPU/driver diversity | CPU fallback, GPU info in diagnostics, compatibility matrix |
| GUI not covered by automation | manual suite, UI import smoke test in CI |
| Physics regressions | numerical unit tests with tolerances, benchmark |
| Slow machines | Performance mode, honest speed display |

## 11. Roles
Maintainers (triage, sign-off), testers (execute, report), developers (fix, add tests).
