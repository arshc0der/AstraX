# Screenshots

The README and docs reference the images in this folder. The files currently here are **placeholders** (dark panels that say "PLACEHOLDER"). Replace each one with a real screenshot **using exactly the same file name**; no other edit is needed.

## How to capture
1. Run `python main.py`, use the default **Mission control (dark)** theme and a window around **1600 x 900** (or capture the region and crop).
2. Windows: `Win + Shift + S`. macOS: `Cmd + Shift + 4`. Linux: your screenshot tool.
3. Save as **PNG**, ideally **1600 x 900** (16:9), under ~1.5 MB (tools like `oxipng`, `pngquant` or squoosh.app shrink them).
4. Do not show personal data (file paths with your name, etc.). Crop the OS taskbar.
5. Commit with the same file name. Run `python tools/check_screenshots.py` to see which are still placeholders.

## Shot list
| File | Title | What to show |
|---|---|---|
| `01-main-window.png` | Main window overview | Whole app: viewport, explorer, right panel, telemetry. Rocket in flight, panels docked. |
| `02-launch-liftoff.png` | Liftoff with Launch camera | Rocket on the pad lifting off, plume visible, banner 'LIFTOFF'. |
| `03-stage-separation.png` | Stage separation | First stage (white dots) falling away after separation, banner visible. |
| `04-rocket-designer.png` | Rocket designer | Designer tab with a loaded example rocket, the 3D preview and the ESTIMATES table. |
| `05-survival-test.png` | Survival test result | Survival dialog showing PASS and the margin table. |
| `06-breakup.png` | Failure / breakup | Vehicle-lost banner with the explosion flash and fragments. |
| `07-flight-safety.png` | Flight safety panel | Load gauges, ABORT button and failure injection. |
| `08-orbit-analysis.png` | Orbit analysis | Orbit change log + maneuver planner with the cyan predicted path in 3D. |
| `09-launch-windows.png` | Launch-window porkchop | Porkchop plot Earth to Mars with the best window circled. |
| `10-mars-transfer.png` | Mars transfer in 3D | Heliocentric view of the transfer trajectory. |
| `11-moon-landing.png` | Powered Moon landing | Lunar lander just before touchdown. |
| `12-telemetry-graphs.png` | Telemetry graphs | Graphs tab: altitude, speed, Mach, heat flux with a compared run. |
| `13-ground-track.png` | Ground track | Trajectory tab on 'Ground track (latitude / longitude)'. |
| `14-planet-inspector.png` | Planet inspector | Mars selected, a MODIFIED flag visible, sources text. |
| `15-studies.png` | Studies | Monte Carlo or parameter-sweep result. |
| `16-settings-graphics.png` | Settings: graphics | Settings dialog with detected GPUs and the Rendering option. |
| `17-multi-window.png` | Multiple windows | Main view plus an extra 3D view and a graph window. |
| `18-splash.png` | Splash screen | The animated splash at startup (grab a frame near the end). |
| `19-themes.png` | Themes | Two or four themes side by side (collage). |
| `20-reentry.png` | Re-entry calculator | Studies > Re-entry with the path plot and results. |

## Optional extras
- A short screen recording (GIF/MP4, <= 15 s) of the first launch: use the app's **Record** button, save as `docs/screenshots/demo.gif`, and add it to the README header.
- Dark and light theme versions for the docs site.
