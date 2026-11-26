# Regression checklist (generated)

All **P1** cases, grouped by area. Run before every release and after changes to the matching area. Tick, then summarise in a *Test report* issue.

## Installation & startup

- [ ] **TC-001** Clean install from requirements - All packages install; the splash and main window appear; no traceback in the terminal
- [ ] **TC-002** Diagnostics report - Prints AstraX version, Python, platform, package versions, GPUs, engine self-test OK; writes diagnostics.txt; no window opens
- [ ] **TC-004** Animated splash - Splash plays the logo animation (~4 s), stays until the window is ready, fades out; background matches the dark theme; no white flash
- [ ] **TC-011** Engine tests pass - All tests pass (no failures/errors)

## Layout & navigation

- [ ] **TC-012** Docks float and re-dock - It floats, then docks; contents intact

## Simulation control

- [ ] **TC-020** Run and pause - Simulation runs; pausing freezes time; resume continues
- [ ] **TC-021** Single step - MET advances by one physics step each press
- [ ] **TC-022** Reset - Back to the pad, MET 0, trail cleared, propellant full
- [ ] **TC-024** Speed presets - Simulation speed changes accordingly; status bar shows requested and achieved speed
- [ ] **TC-027** Honest speed display - If the CPU cannot keep up, achieved < requested is shown; physics accuracy is not reduced

## 3D viewport & cameras

- [ ] **TC-031** Orbit camera - Rotate, zoom and pan work smoothly
- [ ] **TC-032** Launch camera - Camera stays beside the rocket relative to the ground; pad visible at liftoff; plume visible

## Launch & flight

- [ ] **TC-043** Earth launch to LEO - Liftoff banner; first stage separates ~T+147 s; insertion ends ~T+450 s; orbit about 195 x 200 km, e < 0.01
- [ ] **TC-044** Event log and banners - LIFTOFF, STAGE SEPARATION banners; matching timestamped event log lines
- [ ] **TC-045** Jettisoned stage debris - Stage drawn as a white point falling; impact logged later

## Rocket designer

- [ ] **TC-050** Live 3D preview - Preview rebuilds immediately with new dimensions
- [ ] **TC-051** Estimates update - ESTIMATES table (mass, T/W, delta-v, burn time) updates; labelled ESTIMATE
- [ ] **TC-052** Add stage and booster - New items appear in the list and in the 3D model; boosters beside the first stage
- [ ] **TC-054** Example rockets - Each loads, previews and shows plausible estimates; lander shows Launch body = Moon
- [ ] **TC-061** Use in simulation - Simulation restarts with the new design; mass/thrust reflected in telemetry

## Survival test

- [ ] **TC-062** Default rocket passes - PASS ('SURVIVED: stable ~199 x 304 km orbit'); margin table shows all margins positive
- [ ] **TC-063** Thin wall fails - FAIL 'VEHICLE LOST ... structural failure (skin stress ... reached yield)' within ~1 s
- [ ] **TC-064** No active control fails - FAIL 'loss of control (angle of attack ... deg)'

## Flight safety & emergencies

- [ ] **TC-070** Load gauges - Gauges rise and fall; colours change green/amber/red with ratio
- [ ] **TC-071** Abort - Stages jettison, capsule coasts, parachute banner below 7 km, touchdown ~7 m/s, status LANDED
- [ ] **TC-079** Breakup visuals - VEHICLE LOST banner with reason; flash and fragments; run ends after the debris falls

## Orbit analysis

- [ ] **TC-080** Orbit change log - Rows for each phase change and separation; perigee rises to ~195 km
- [ ] **TC-081** Maneuver preview - After-orbit apogee higher than before; table shows both

## Planets & solar system

- [ ] **TC-086** Earth values - Surface gravity about 9.82 m/s2; mean density about 5514 kg/m3; period about 365.25 d; sources shown
- [ ] **TC-087** Edit mass restarts - Status MODIFIED; simulation restarts; Mars orbit behaves accordingly
- [ ] **TC-088** Reset body / all - Values restored; MODIFIED flag clears

## Launch windows

- [ ] **TC-091** Porkchop computes - Heat-map appears; best window circled; progress bar shows then hides
- [ ] **TC-092** Best window values - Departure about day 469 (April 2001), flight about 200 d, v-infinity about 3.5 km/s, synodic period about 780 d

## Landing, studies & challenges

- [ ] **TC-096** Moon powered descent - Lander replaces the rocket; LANDING BURN ignition ~2 km up; LANDED under 10 m/s; propellant left about 4.4 t
- [ ] **TC-102** Re-entry calculator - Peak about 8-9 g near 39 km, peak heat flux about 560 kW/m2, plot of the path

## Telemetry & export

- [ ] **TC-103** Live readouts - Live values update (altitude, speed, Mach, thrust, fuel...)
- [ ] **TC-104** Graph variables - Graphs redraw with correct axis labels and units
- [ ] **TC-106** CSV export - File opens in a spreadsheet; headers include units; values match the graphs

## Settings & graphics

- [ ] **TC-112** Theme switch - Theme applies immediately (UI colours); Light theme keeps the 3D background dark
- [ ] **TC-115** Renderer shown - Shows 'GPU: <device>' (green) or 'CPU rendering: <device>' (amber); same line in the log
- [ ] **TC-116** Rendering mode switch - Restart prompt; after restart status bar shows CPU rendering; GPU mode restores hardware

## Files & compatibility

- [ ] **TC-122** Scenario round trip - Rocket, launch, plan and planet edits restored
- [ ] **TC-124** Invalid file handled - Clear error message; app continues

## Robustness & performance

- [ ] **TC-132** Rapid reset/run - No crash or hang

Total P1 cases: 44 of 140.
