# Architecture decision records (ADR log)

Short records of significant decisions. Add a new entry (status: proposed/accepted/superseded) for any breaking or far-reaching change.

| # | Decision | Status |
|---|---|---|
| 1 | **PyQt6 desktop UI** with pyqtgraph/OpenGL (original project requirement; no web UI) | accepted |
| 2 | **Engine separated from UI**: `astrax/` has no Qt imports; testable headless | accepted |
| 3 | **Simulation on a worker thread**; UI communicates by command queue and immutable snapshots | accepted |
| 4 | **Snapshot back-pressure** (`ack`) so frames never queue faster than the GUI draws | accepted |
| 5 | **SI units internally**, ecliptic J2000 barycentric frame | accepted |
| 6 | **Integrators**: RK4 (default), DOPRI5 (adaptive), Verlet (symplectic) selectable | accepted |
| 7 | **Auto time step** from orbit, atmosphere, drag relaxation, ground-approach scales; never coarsen physics to hit a playback speed | accepted |
| 8 | **Zero-order-hold guidance/throttle per step**, mass integrated exactly (constant ṁ per step) | accepted |
| 9 | **Mean Keplerian elements** for planets (documented limitation) rather than bundling an ephemeris | accepted |
| 10 | **Simplified structure model** (yield-stress screening) with explicit limits; failures end the run with debris | accepted |
| 11 | **Splash/logo pre-rendered** from SVG with Chromium (Qt SVG ignores blur filters and `animateMotion`); theme colour baked in | accepted |
| 12 | **GPU/CPU backend chosen before `QApplication`** (Auto/GPU/CPU), restart to change | accepted |
| 13 | **Generated docs** (API, formats, validation, test cases) so they cannot drift | accepted |
| 14 | **JSON formats with `astrax_format` tags** and defaults for new fields (backward compatible) | accepted |
| 15 | **MIT license for AstraX; PyQt6 is GPL/commercial** → documented in THIRD_PARTY_NOTICES; PySide6 evaluation on the roadmap | accepted |
| 16 | **Legacy engine kept in `legacy/`** for reference only | accepted |

## Template
```
### ADR-N: Title
Status: proposed | accepted | superseded by ADR-M
Context: what problem/forces?
Decision: what we do.
Consequences: good, bad, follow-ups.
```
