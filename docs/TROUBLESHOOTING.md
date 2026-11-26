# Troubleshooting

Start with `python main.py --diagnostics` - it prints versions, GPUs and an engine self-test. Attach its output to any bug report.

## 1. Installation and startup
| Symptom | Cause / fix |
|---|---|
| `pip.exe ... Application Control policy has blocked this file` | use `python -m pip install -r requirements.txt` |
| `ImportError: DLL load failed while importing QtWidgets` | security software/policy blocked a Qt DLL; retry, allow the `venv` folder, or reinstall: `python -m pip install --force-reinstall PyQt6` |
| `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` (Linux) | `sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libgl1 libegl1`; on Wayland try `QT_QPA_PLATFORM=xcb` |
| `ModuleNotFoundError: No module named 'PyQt6'` | the virtual environment is not active, or requirements were not installed |
| App closes immediately without a window | run from a terminal to see the traceback; add it to a bug report |
| Python too old | AstraX needs Python 3.10+ (`python --version`) |

## 2. Graphics and 3D view
| Symptom | Fix |
|---|---|
| Blank/black 3D view | update the GPU driver; `python main.py --cpu`; report `--diagnostics` |
| Status bar says "CPU rendering" | Settings ▸ Graphics ▸ Rendering = GPU, restart |
| GPU usage 0 % | see [GRAPHICS_AND_PERFORMANCE](GRAPHICS_AND_PERFORMANCE.md) (physics is CPU; dual-GPU laptops need *Prefer high-performance GPU*) |
| Window larger than the screen | *View ▸ Reset window layout*, restart |
| Text too small/large on a 4K screen | Settings ▸ font size; `QT_SCALE_FACTOR=1.25 python main.py` |
| Dark title bar missing | works on Windows 10 1809+/11 only |
| Splash flickers or is slow | `--no-splash` or Settings ▸ untick splash |

## 3. Performance
| Symptom | Fix |
|---|---|
| Lag / low FPS | Settings ▸ Graphics ▸ Performance quality, FPS cap 20; close extra windows; hide labels/atmosphere layers; check `UI xx ms` in the status bar |
| "Accel: requested 1000x / achieved 80x" | the CPU cannot run physics that fast; AstraX never lowers accuracy to catch up; lower the speed |
| High CPU while paused | use a lower FPS cap; close graph windows |

## 4. Simulation behaviour
| Symptom | Explanation / fix |
|---|---|
| Rocket does not leave the pad | T/W < 1 for the launch body; add thrust/remove mass ([designer estimates](UI_REFERENCE.md)) |
| Survival test: LOST at T+1 s | wall too thin for the loads (stress reached yield): increase wall thickness/dry mass consistent with it |
| Survival test: LOST by "loss of control" | design is aerodynamically unstable and *Active attitude control* is off |
| Survival: "did not reach orbit" with a good design | standard ascent profile may not fit it; try other kick angles via *Parameter sweep* or write your own plan |
| Orbit decays / crashes after a burn | periapsis inside the atmosphere; raise it with a prograde burn at apoapsis |
| "dt too large" warning | set *dt mode = auto* |
| Planet positions differ from an almanac | mean-element model (arc-minute errors); see [PHYSICS](PHYSICS.md) |
| Transfer misses Mars by ~2 million km | expected: no mid-course correction is modelled in that preset |

## 5. Files and data
| Symptom | Fix |
|---|---|
| "Not an AstraX scenario file" | wrong file type; scenario/rocket/session/planet files have different format tags ([FILE_FORMATS](FILE_FORMATS.md)) |
| Old file loads with defaults for new fields | expected: formats are backwards compatible |
| CSV opens with strange headers | headers contain units, e.g. `altitude_m [m]` |
| GIF is huge | lower the viewport size or record shorter clips |
| MP4 recording fails | install `ffmpeg` and put it on PATH; GIF always works |

## 6. Reset everything
- Settings: delete the Qt settings (Windows registry `HKCU\Software\AstraX`; Linux `~/.config/AstraX`; macOS `~/Library/Preferences/com.AstraX.*`).
- Layout: *View ▸ Reset window layout*.
- Logs: delete the `logs/` folder.

## 7. Still stuck?
Open a [bug report](https://github.com/arshc0der/AstraX/issues/new/choose) with: `diagnostics.txt`, the traceback, steps to reproduce and a screenshot. How to write a great one: [tester/BUG_REPORTING.md](tester/BUG_REPORTING.md).
