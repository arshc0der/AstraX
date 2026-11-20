# UI reference

Every control, by location. Hover any control in the app for a tooltip.

## Toolbar
| Control | Action |
|---|---|
| Run / Pause (`Space`) | start or pause the simulation |
| Step (`N`) | one physics step while paused |
| Stop | pause and hold |
| Reset (`R`) | back to the launch conditions |
| Stage (`S`) | manual separation (boosters first, then the lowest core stage) |
| Slower / Faster (`-` / `+`) | previous / next speed in the list |
| Speed box | 0.1×, 0.5×, 1×, 2×, 5×, 10×, 50×, 100×, 1000×, **Custom...** (any value) |
| Integrator | `rk4`, `dopri5` (adaptive), `verlet` (symplectic) |
| dt mode / dt | `auto` sizes the step from orbit, atmosphere, drag and ground-approach time scales; `fixed` uses your value and shows stability warnings |
| Camera | Orbit, Free, Follow rocket, Follow selected body, First person, Launch camera (locked relative to the ground) |
| Top / Side / Front / Iso | camera presets |
| Reset cam (`Home`) / Focus (`F`) | recentre / focus the selected body |
| Record | start/stop viewport recording → GIF or MP4 (needs ffmpeg) |
| Snapshot | save a PNG of the viewport |

## Status bar
Simulation time · mission elapsed time · requested vs **achieved** speed · current dt and integrator · physics steps/s · FPS · numerics status (green "numerics OK" or the first warning).

## Menus
- **File**: new/open/save scenario, export telemetry CSV, export mission report, save/load session, exit.
- **View**: visualisation layers (planet orbits, trajectory, velocity/acceleration/gravity vectors, atmosphere boundary, axes, labels, info overlay, grid), body-size exaggeration, reset layout, dock toggles.
- **Window**: new 3D view window, new graph window, close all extra windows.
- **Tools**: design survival test, settings & customisation, open logs folder.
- **Help**: About (logo and version).

## Centre tabs
### Simulation
The 3D viewport plus an overlay (status, time, body, altitude, speed, scale factors) and event banners.

### Rocket designer
| Area | Controls |
|---|---|
| Structure | stage list; **+ Stage**, **+ Booster**, Duplicate, Remove, Up, Down |
| Example rockets | six illustrative designs + **Load** |
| Files | save/load JSON, import OBJ, export OBJ |
| **Will it survive?** | opens the survival test |
| **Use this rocket in simulation** | restarts the simulation with this design |
| Vehicle | payload, Cd, nose shape/length/mass, **launch body**, nose-tip radius, active control |
| Selected stage | name, diameter, length, interstage, dry mass, fuel, capacity, booster copies, separation rule/time, **material, wall thickness**, shell-mass estimate, colour |
| Engines | count, placement, thrust, Isp (vac/SL), derived ṁ, nozzle size |
| Fins & legs | counts and geometry |
| Design limits | max-Q, max axial g, max heat flux, factor of safety |
| Estimates table | **ESTIMATES** only: mass, mass ratio, T/W, Δv, burn time, max acceleration, CoM, CoP, static margin, inertia, per-stage Δv |

### Learn
Equations with live numbers: gravity, orbits, rocket equation, T/W, Δv budget, Hohmann, drag, aerodynamics, structural loads, orbit changes.

## Right panel tabs
### Mission control
Launch tab (body, destination, start mode `pad/orbit/hover/transfer`, lat/lon, azimuth, start altitude/distance, **start epoch**, extra velocity), Flight plan table (+ Apply to simulation), Flight computer (Python script).

### Planet inspector
Edit mass, radius, rotation period, tilt, orbital elements; derived values; atmosphere; sources; **Reset to default / Reset ALL**; save/load planet JSON.

### Flight safety
Four load gauges, **ABORT**, engine cutoff, failure injection (engine out, leak, stuck throttle, guidance lost, clear), realism options (aerodynamics model, autopilot protection, failures on/off).

### Orbit analysis
Orbit-change log + perigee/apogee graph; maneuver planner (preview, predicted path, apply impulse); Hohmann helper.

### Launch windows
Pick planets, search range, flight-time range, grid; **porkchop** heat-map (total Δv), best window summary, **Fly best transfer in 3D**.

### Studies
Max payload · Parameter sweep · Monte Carlo · Re-entry calculator.

### Challenges
First orbit, Gentle ascent, Moon soft landing, Abort at max-Q: **Run** for a verdict or **Load in 3D**.

## Bottom panel
- **Telemetry**: Live readouts; Graphs (four selectable variables incl. Mach, AoA, heat flux, stress, latitude/longitude; compare runs; CSV/session export); Trajectory & travel analysis (relative orbit, heliocentric, distance vs time, **ground track**).
- **Event log**: all events, timestamped.

## Settings (Tools ▸ Settings)
Theme (Mission control dark · Midnight blue · High contrast · Light), font size, trail length, planet size exaggeration, **animated splash on/off**, engine plume, telemetry sample interval. Saved between runs.
