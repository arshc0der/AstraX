# Performance testing

## 1. What to measure
| Metric | Where | Target (typical laptop, Quality mode) |
|---|---|---|
| **UI ms** (GUI time per frame) | status bar | < 20 ms (smooth), < 33 ms (acceptable) |
| **FPS** | status bar | ≥ 25 at 30 fps cap |
| **Physics steps/s** | status bar | see engine numbers below |
| **Achieved vs requested speed** | status bar | achieved ≈ requested up to 100x on a modern CPU |
| **Start-up time** | stopwatch to usable window | < 10 s with splash |
| **Memory** | OS task manager | < 600 MB after 30 min |
| **CPU when paused** | task manager | low (< 10 % of one core) |

## 2. Engine benchmark (no GUI)
```bash
python tools/benchmark.py     # writes benchmark.json
```
Reference run in the CI-like Linux sandbox used for development (Python 3.12, one shared CPU core - **your results will differ**):

| Benchmark | Time | Steps | Steps/s |
|---|---|---|---|
| Full ascent to orbit (auto dt) | 3.1 s | 4,518 | ~1,470 |
| 30-day N-body coast (RK4, dt 600 s) | 1.1 s | 4,320 | ~3,880 |
| Survival test (demo rocket) | 2.9 s | - | - |
| Porkchop 30×30 Earth→Mars | 0.23 s | - | - |

Report regressions larger than **25 %** on the same machine.

## 3. GUI performance scenarios
| ID | Scenario | Procedure | Record |
|---|---|---|---|
| P-1 | Idle | start the app, do nothing 2 min | CPU %, memory, UI ms |
| P-2 | LEO flight 1x | LEO preset at 1x | UI ms, FPS, steps/s |
| P-3 | LEO flight 100x | same at 100x | achieved speed, UI ms |
| P-4 | Sun dive 1000x | preset, 150 simulated days | achieved speed, memory growth |
| P-5 | Multi-window | add 2 extra 3D views + 2 graph windows during P-2 | UI ms |
| P-6 | Performance mode | repeat P-2 with Quality = Performance | UI ms delta |
| P-7 | CPU rendering | `--cpu` + P-2 | UI ms (expect higher) |
| P-8 | GPU vs iGPU (dual-GPU laptops) | repeat P-2 with *Prefer high-performance GPU* off/on | UI ms, GPU engine usage in Task Manager |

## 4. How to read GPU usage correctly
Only 3D drawing uses the GPU; a small scene needs little. In Task Manager: *Performance ▸ GPU n ▸ 3D engine*. On laptops **GPU 0** is often the integrated chip. See [GRAPHICS_AND_PERFORMANCE](../GRAPHICS_AND_PERFORMANCE.md).

## 5. Reporting template
```
Build: 4.0.0   OS/Python: Windows 11 / 3.12   CPU: i7-1165G7   GPU: Iris Xe + RTX 3050
Mode: Auto/GPU, Quality, 30 fps cap
P-2: UI 11 ms, FPS 30, steps/s 1900
P-3: requested 100x achieved 100x, UI 14 ms
P-4: achieved 640x of 1000x, memory 310 MB (+12 MB / 10 min)
Notes: ...
```
Attach `benchmark.json` and `diagnostics.txt`.

## 6. Known performance characteristics
- Physics is Python/NumPy; time acceleration 1000x may not be reachable on slow CPUs (the app says so rather than losing accuracy).
- Telemetry graphs redraw only when visible; extra 3D windows each add GPU/CPU load.
- Software OpenGL (`--cpu`) is several times slower than hardware rendering.
