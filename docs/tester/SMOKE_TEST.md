# Smoke test (10-15 minutes, generated)

Run this on every release candidate and after any risky merge. If any step fails, stop and report - the build is not ready for wider testing.

| # | Test case | Do | Expect | Result |
|---|---|---|---|---|
| 1 | **TC-001** Clean install from requirements | Create a new venv; `python -m pip install -r requirements.txt`; `python main.py` | All packages install; the splash and main window appear; no traceback in the terminal | ☐ |
| 2 | **TC-002** Diagnostics report | Run `python main.py --diagnostics` | Prints AstraX version, Python, platform, package versions, GPUs, engine self-test OK; writes diagnostics.txt; no window opens | ☐ |
| 3 | **TC-004** Animated splash | Start the app | Splash plays the logo animation (~4 s), stays until the window is ready, fades out; background matches the dark theme; no white flash | ☐ |
| 4 | **TC-043** Earth launch to LEO | Load preset; Run until phase 'Parked in orbit' | Liftoff banner; first stage separates ~T+147 s; insertion ends ~T+450 s; orbit about 195 x 200 km, e < 0.01 | ☐ |
| 5 | **TC-050** Live 3D preview | Designer: change stage length/diameter | Preview rebuilds immediately with new dimensions | ☐ |
| 6 | **TC-051** Estimates update | Change engine count and propellant | ESTIMATES table (mass, T/W, delta-v, burn time) updates; labelled ESTIMATE | ☐ |
| 7 | **TC-062** Default rocket passes | Designer > Will it survive? > Run | PASS ('SURVIVED: stable ~199 x 304 km orbit'); margin table shows all margins positive | ☐ |
| 8 | **TC-063** Thin wall fails | Set wall thickness 0.5 mm on all stages; run | FAIL 'VEHICLE LOST ... structural failure (skin stress ... reached yield)' within ~1 s | ☐ |
| 9 | **TC-071** Abort | During first-stage burn (~T+60 s) press ABORT | Stages jettison, capsule coasts, parachute banner below 7 km, touchdown ~7 m/s, status LANDED | ☐ |
| 10 | **TC-096** Moon powered descent | Load 'Moon powered descent'; Run | Lander replaces the rocket; LANDING BURN ignition ~2 km up; LANDED under 10 m/s; propellant left about 4.4 t | ☐ |
| 11 | **TC-091** Porkchop computes | Launch windows > Earth to Mars, start 0, span 800, flight 120-350 > Compute | Heat-map appears; best window circled; progress bar shows then hides | ☐ |
| 12 | **TC-080** Orbit change log | After the LEO flight open Orbit analysis > Orbit changes | Rows for each phase change and separation; perigee rises to ~195 km | ☐ |
| 13 | **TC-086** Earth values | Planet inspector > Earth | Surface gravity about 9.82 m/s2; mean density about 5514 kg/m3; period about 365.25 d; sources shown | ☐ |
| 14 | **TC-104** Graph variables | Graphs tab: change each of the four variable selectors | Graphs redraw with correct axis labels and units | ☐ |
| 15 | **TC-106** CSV export | Export telemetry CSV | File opens in a spreadsheet; headers include units; values match the graphs | ☐ |
| 16 | **TC-115** Renderer shown | Look at the status bar after start | Shows 'GPU: <device>' (green) or 'CPU rendering: <device>' (amber); same line in the log | ☐ |
| 17 | **TC-122** Scenario round trip | File > Save scenario; New; Open scenario | Rocket, launch, plan and planet edits restored | ☐ |
| 18 | **TC-135** Close while running | Close the window during a run | App exits cleanly within ~2 s; no zombie process | ☐ |

Time box: 15 minutes. Record the environment (OS, Python, GPU, AstraX version) in the report.
