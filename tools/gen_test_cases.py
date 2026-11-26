"""Generate docs/tester/MANUAL_TEST_CASES.md and docs/tester/test_cases.csv from the test-case data below.   python tools/gen_test_cases.py"""
import csv, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); OUT = os.path.join(ROOT, "docs", "tester")
CASES = []


def T(area, pri, title, steps, expected, pre=""):
    CASES.append(dict(area=area, pri=pri, title=title, pre=pre or "App started (`python main.py`)", steps=[s.strip() for s in steps.split(";") if s.strip()], expected=expected))


A = "Installation & startup"
T(A, "P1", "Clean install from requirements", "Create a new venv; `python -m pip install -r requirements.txt`; `python main.py`", "All packages install; the splash and main window appear; no traceback in the terminal", "Fresh machine/venv")
T(A, "P1", "Diagnostics report", "Run `python main.py --diagnostics`", "Prints AstraX version, Python, platform, package versions, GPUs, engine self-test OK; writes diagnostics.txt; no window opens", "Terminal")
T(A, "P2", "GPU listing", "Run `python main.py --gpu-info`", "Lists installed GPUs with kind (discrete/integrated) and what Auto would choose; no window opens", "Terminal")
T(A, "P1", "Animated splash", "Start the app", "Splash plays the logo animation (~4 s), stays until the window is ready, fades out; background matches the dark theme; no white flash")
T(A, "P2", "Skip splash", "Run `python main.py --no-splash`", "Main window opens directly")
T(A, "P2", "Splash setting", "Tools > Settings > untick splash > Apply; restart", "No splash on next start; re-enable restores it")
T(A, "P2", "Window and taskbar icon", "Start the app; look at the title bar and taskbar/dock", "The AstraX emblem icon is shown (not the Python/Qt default)")
T(A, "P2", "Default dark theme", "Start the app with cleared settings", "Dark 'Mission control' theme; menus, dialogs and scroll bars are dark too", "Settings cleared")
T(A, "P3", "Themed title bar (Windows)", "Start the app on Windows 10/11", "Native title bar is dark/theme coloured; same for dialogs and floating windows", "Windows only")
T(A, "P3", "About dialog", "Help > About AstraX", "Shows the full logo, version 4.0.0 and the accuracy disclaimer; Close works")
T(A, "P1", "Engine tests pass", "Run `python -m unittest discover -s tests -v`", "All tests pass (no failures/errors)", "Terminal, no GUI")

A = "Layout & navigation"
T(A, "P1", "Docks float and re-dock", "Drag the right panel title out of the window; drag it back", "It floats, then docks; contents intact")
T(A, "P2", "Dock tabs", "Drag Event log onto Telemetry", "They tab together; switching tabs works")
T(A, "P2", "Reset layout", "View > Reset window layout; restart", "Default layout returns")
T(A, "P2", "Window fits a 1366x768 screen", "Start on/emulate a 1366x768 display", "Window fits; panels scroll instead of forcing a larger window")
T(A, "P2", "Menus complete", "Open File, View, Window, Tools, Help", "All items listed in UI_REFERENCE exist and open without error")
T(A, "P2", "Status bar fields", "Run a simulation", "Shows sim time, MET, requested vs achieved speed, dt/integrator, steps/s, FPS, UI ms, GPU/CPU renderer, numerics status")
T(A, "P2", "Tooltips", "Hover toolbar buttons and designer fields", "Tooltips describe the control (and shortcut)")
T(A, "P2", "Keyboard shortcuts", "Press Space, N, R, S, +, -, F, Home", "Each performs the action in KEYBOARD_SHORTCUTS.md")

A = "Simulation control"
T(A, "P1", "Run and pause", "Load 'Earth launch to LEO'; Space; Space", "Simulation runs; pausing freezes time; resume continues")
T(A, "P1", "Single step", "Pause; press N several times", "MET advances by one physics step each press")
T(A, "P1", "Reset", "Run for 30 s; press R", "Back to the pad, MET 0, trail cleared, propellant full")
T(A, "P2", "Stop", "Run; press Stop", "Simulation pauses and holds state")
T(A, "P1", "Speed presets", "Select 0.1x, 1x, 10x, 100x, 1000x in turn", "Simulation speed changes accordingly; status bar shows requested and achieved speed")
T(A, "P2", "Custom speed", "Speed box > Custom... > 25", "Runs at 25x; value accepted; invalid values rejected")
T(A, "P2", "Slower/Faster buttons", "Click Faster and Slower", "Speed steps through the list")
T(A, "P1", "Honest speed display", "Set 1000x on a slow machine", "If the CPU cannot keep up, achieved < requested is shown; physics accuracy is not reduced")
T(A, "P2", "Integrator switch", "Switch rk4 / dopri5 / verlet while paused, run", "All run; orbit stays circular in the orbit-start scenario")
T(A, "P2", "Fixed dt warning", "dt mode fixed; dt = 600 s on a LEO orbit start", "Status bar shows an ERROR/WARNING about dt too large; auto mode clears it")
T(A, "P2", "Manual stage", "During first-stage burn press S", "Stage separates; banner and event log entry appear")

A = "3D viewport & cameras"
T(A, "P1", "Orbit camera", "Orbit camera; left-drag, wheel, middle-drag", "Rotate, zoom and pan work smoothly")
T(A, "P1", "Launch camera", "Camera > Launch camera; run the LEO preset", "Camera stays beside the rocket relative to the ground; pad visible at liftoff; plume visible")
T(A, "P2", "Follow rocket", "Camera > Follow rocket", "Camera follows the vehicle")
T(A, "P2", "Follow selected body", "Select Mars in the Explorer; Camera > Follow selected body", "Camera focuses Mars")
T(A, "P3", "First person", "Camera > First person", "View from the rocket along its axis; switch back works")
T(A, "P2", "View presets", "Click Top, Side, Front, Iso", "Camera snaps to each view")
T(A, "P2", "Reset camera and focus", "Home; F with a body selected", "Camera recenters / focuses")
T(A, "P2", "Layers toggles", "View > Visualisation layers: toggle each", "Orbits, trail, vectors, atmosphere shell, axes, labels, overlay, grid appear/disappear independently")
T(A, "P3", "Body size exaggeration", "View > Body size exaggeration > 10", "Planets draw larger; rocket scale label updates")
T(A, "P2", "Snapshot", "Toolbar Snapshot > save", "PNG of the viewport is saved and opens")
T(A, "P2", "Record GIF", "Toolbar Record; run 5 s; Record again > save .gif", "GIF saved; plays the viewport animation")
T(A, "P3", "Record MP4 without ffmpeg", "Record > save as .mp4 without ffmpeg installed", "Clear message that ffmpeg is needed; app stays responsive")

A = "Launch & flight"
T(A, "P1", "Earth launch to LEO", "Load preset; Run until phase 'Parked in orbit'", "Liftoff banner; first stage separates ~T+147 s; insertion ends ~T+450 s; orbit about 195 x 200 km, e < 0.01", "Default rocket")
T(A, "P1", "Event log and banners", "Watch the LEO flight", "LIFTOFF, STAGE SEPARATION banners; matching timestamped event log lines")
T(A, "P1", "Jettisoned stage debris", "After separation observe the scene", "Stage drawn as a white point falling; impact logged later")
T(A, "P2", "Plume follows throttle", "Observe during throttle-down / coast", "Plume length changes with throttle; disappears with engines off")
T(A, "P2", "Flight-plan edit", "Edit a phase's 'Ends when' JSON; Apply; run", "New plan used; invalid JSON shows a clear error")
T(A, "P2", "Orbit start", "Mission control > start mode orbit, altitude 400 km; Apply", "Starts in a circular orbit; period about 92.6 min; e near 0")
T(A, "P2", "Sun-dive preset", "Load 'LEO -> Sun dive'; run 150 days at high speed", "Distance from the Sun drops to about 0.34 AU then rises")

A = "Rocket designer"
T(A, "P1", "Live 3D preview", "Designer: change stage length/diameter", "Preview rebuilds immediately with new dimensions")
T(A, "P1", "Estimates update", "Change engine count and propellant", "ESTIMATES table (mass, T/W, delta-v, burn time) updates; labelled ESTIMATE")
T(A, "P1", "Add stage and booster", "+ Stage; + Booster", "New items appear in the list and in the 3D model; boosters beside the first stage")
T(A, "P2", "Remove/duplicate/reorder", "Duplicate, Up, Down, Remove a stage", "List and model update consistently; cannot remove the last stage")
T(A, "P1", "Example rockets", "Load each of the 6 examples", "Each loads, previews and shows plausible estimates; lander shows Launch body = Moon")
T(A, "P2", "Engine placement", "Set placement single / ring / octaweb / cluster", "Nozzle layout in the model changes")
T(A, "P2", "Nose shapes", "Cycle all 5 nose shapes", "Shape changes; no mesh errors")
T(A, "P2", "T/W validation", "Set engine count to 1 on the default rocket", "Warning 'cannot lift off from Earth'; status text turns amber")
T(A, "P2", "Wall thickness warning", "Set a very thick wall with low dry mass", "Warning that the shell mass is close to/above the dry mass")
T(A, "P2", "Save/load design", "Save JSON; change design; load JSON", "Original design restored exactly")
T(A, "P2", "OBJ export/import", "Export OBJ; import it back", "File opens in a 3D tool; import adds the custom mesh without crashing")
T(A, "P1", "Use in simulation", "Edit a design; 'Use this rocket in simulation'", "Simulation restarts with the new design; mass/thrust reflected in telemetry")

A = "Survival test"
T(A, "P1", "Default rocket passes", "Designer > Will it survive? > Run", "PASS ('SURVIVED: stable ~199 x 304 km orbit'); margin table shows all margins positive", "Default rocket")
T(A, "P1", "Thin wall fails", "Set wall thickness 0.5 mm on all stages; run", "FAIL 'VEHICLE LOST ... structural failure (skin stress ... reached yield)' within ~1 s")
T(A, "P1", "No active control fails", "Untick Active attitude control; run", "FAIL 'loss of control (angle of attack ... deg)'", "Default rocket")
T(A, "P2", "Max-Q overload", "Max dynamic pressure 15 kPa; untick autopilot protection in the dialog; run", "FAIL 'aerodynamic overload'")
T(A, "P2", "Cannot lift off", "Set engine count 1; run", "Result 'Cannot lift off: sea-level thrust-to-weight is ...'")
T(A, "P2", "Watch in 3D", "After a result click 'Watch this launch in 3D'", "Main window loads the scenario and plays it with launch camera; failures show breakup animation")
T(A, "P2", "Dialog stays responsive", "Run the test and move the window", "UI does not freeze; progress shown")
T(A, "P3", "Sounding rocket / SSTO", "Run the test on the sounding rocket and the SSTO example", "Neither is reported SURVIVED (suborbital / fails to reach orbit)")

A = "Flight safety & emergencies"
T(A, "P1", "Load gauges", "Run LEO; watch Flight safety gauges", "Gauges rise and fall; colours change green/amber/red with ratio")
T(A, "P1", "Abort", "During first-stage burn (~T+60 s) press ABORT", "Stages jettison, capsule coasts, parachute banner below 7 km, touchdown ~7 m/s, status LANDED")
T(A, "P2", "Engine cutoff", "Press Engine cutoff in flight", "Thrust goes to zero; plume disappears")
T(A, "P2", "Engine out", "Press Engine out", "Thrust drops by 1/9 on the demo rocket; event logged")
T(A, "P2", "Propellant leak", "Start leak 300 kg/s", "Propellant falls faster; mass decreases without thrust")
T(A, "P2", "Throttle stuck", "Throttle stuck at 1.0 / 0.5", "Throttle ignores the flight plan")
T(A, "P2", "Guidance lost", "Press Guidance lost", "Attitude frozen at last direction; trajectory deviates")
T(A, "P2", "Clear faults", "Press Clear all faults", "Status returns to 'Systems nominal'")
T(A, "P2", "Realism toggles", "Switch aerodynamics advanced/simple; toggle protection and failures", "Behaviour changes accordingly (e.g. failures off lets overloaded vehicles survive)")
T(A, "P1", "Breakup visuals", "Run a failing design in 3D", "VEHICLE LOST banner with reason; flash and fragments; run ends after the debris falls")

A = "Orbit analysis"
T(A, "P1", "Orbit change log", "After the LEO flight open Orbit analysis > Orbit changes", "Rows for each phase change and separation; perigee rises to ~195 km")
T(A, "P1", "Maneuver preview", "Orbit start; prograde +100 m/s; Preview", "After-orbit apogee higher than before; table shows both")
T(A, "P2", "Predicted path", "Draw predicted path", "Cyan ellipse drawn in 3D; Clear path removes it; simulation state unchanged")
T(A, "P2", "Apply impulse", "Apply impulse now", "Orbit changes in the running simulation; event logged")
T(A, "P2", "Plane change", "Equatorial orbit; normal +v*tan(5 deg)", "Inclination increases by about 5 deg in preview")
T(A, "P2", "Hohmann helper", "Target altitude 1000 km > Compute", "dv1/dv2/time shown; prograde field filled")

A = "Planets & solar system"
T(A, "P1", "Earth values", "Planet inspector > Earth", "Surface gravity about 9.82 m/s2; mean density about 5514 kg/m3; period about 365.25 d; sources shown")
T(A, "P1", "Edit mass restarts", "Change Mars mass +50 %; commit", "Status MODIFIED; simulation restarts; Mars orbit behaves accordingly")
T(A, "P1", "Reset body / all", "Reset to default; Reset ALL", "Values restored; MODIFIED flag clears")
T(A, "P2", "Save/load planets", "Save planet config; change; load", "Edited values restored")
T(A, "P2", "Explorer focus", "Double-click Jupiter in the Explorer", "Inspector selects Jupiter and the camera focuses it")

A = "Launch windows"
T(A, "P1", "Porkchop computes", "Launch windows > Earth to Mars, start 0, span 800, flight 120-350 > Compute", "Heat-map appears; best window circled; progress bar shows then hides")
T(A, "P1", "Best window values", "Read the summary", "Departure about day 469 (April 2001), flight about 200 d, v-infinity about 3.5 km/s, synodic period about 780 d")
T(A, "P2", "Fly transfer in 3D", "Fly best transfer in 3D", "Heliocentric view starts; time accel 2,000,000x; distance to Mars decreases; closest approach about 2 million km")
T(A, "P3", "Other planet pairs", "Earth to Venus and Earth to Jupiter", "Results appear (or a clear 'no valid transfers' message); no crash")
T(A, "P3", "Same planet selected", "Choose Earth to Earth", "Message 'Choose two different planets'")

A = "Landing, studies & challenges"
T(A, "P1", "Moon powered descent", "Load 'Moon powered descent'; Run", "Lander replaces the rocket; LANDING BURN ignition ~2 km up; LANDED under 10 m/s; propellant left about 4.4 t")
T(A, "P2", "Challenges headless", "Challenges > run each", "First orbit, Gentle ascent, Moon soft landing, Abort at max-Q all PASS on defaults; message shown")
T(A, "P2", "Challenge load in 3D", "Load in 3D for each challenge", "Scenario prepared (rocket + preset); runs")
T(A, "P2", "Max payload", "Studies > Max payload", "Returns a number in kg and a note; UI stays responsive")
T(A, "P2", "Parameter sweep", "Sweep payload_mass_kg 2000..14000, 8 steps", "Table and plot fill; low payloads SURVIVED, high ones not")
T(A, "P2", "Monte Carlo", "20 runs default sigmas", "Success rate and verdict counts shown; same seed reproduces")
T(A, "P1", "Re-entry calculator", "Earth, 5000 kg, Cd 1.3, A 12, Rn 4.7, 7800 m/s, 2 deg", "Peak about 8-9 g near 39 km, peak heat flux about 560 kW/m2, plot of the path")

A = "Telemetry & export"
T(A, "P1", "Live readouts", "Run a flight", "Live values update (altitude, speed, Mach, thrust, fuel...)")
T(A, "P1", "Graph variables", "Graphs tab: change each of the four variable selectors", "Graphs redraw with correct axis labels and units")
T(A, "P2", "Compare runs", "Keep run; change design; run; tick both", "Both curves overlay with different colours/styles")
T(A, "P1", "CSV export", "Export telemetry CSV", "File opens in a spreadsheet; headers include units; values match the graphs")
T(A, "P2", "Session save/load", "Save session; load it", "Appears in the comparison list and plots")
T(A, "P2", "Mission report", "File > Export mission report", "Markdown with estimates and results in separate sections (+ PNG if matplotlib installed)")
T(A, "P2", "Trajectory modes", "Trajectory tab: all four modes", "Relative, heliocentric, distance-vs-time and ground track plots render")
T(A, "P2", "Ground track", "Ground track after the LEO flight", "Track starts at 28.5 N, 80.6 W and moves east")
T(A, "P3", "Run logs", "Tools > Open logs folder", "Folder opens with a timestamped log containing OpenGL renderer line and events")

A = "Settings & graphics"
T(A, "P1", "Theme switch", "Settings > each theme > Apply", "Theme applies immediately (UI colours); Light theme keeps the 3D background dark")
T(A, "P2", "Font size", "Settings > font 8 and 16", "Interface text scales; layout remains usable")
T(A, "P2", "Trail length", "Set trail 500 vs 20000", "Trail length changes in the 3D view")
T(A, "P1", "Renderer shown", "Look at the status bar after start", "Shows 'GPU: <device>' (green) or 'CPU rendering: <device>' (amber); same line in the log")
T(A, "P1", "Rendering mode switch", "Settings > Rendering = CPU > Apply > restart", "Restart prompt; after restart status bar shows CPU rendering; GPU mode restores hardware")
T(A, "P2", "Prefer discrete GPU", "Tick option; restart (dual-GPU laptop)", "Task Manager shows python.exe on the discrete GPU (GPU 1)", "Dual-GPU laptop")
T(A, "P2", "Performance quality", "Visual quality = Performance", "Labels, atmosphere shells and antialiasing off; lower sphere detail; smoother on weak GPUs")
T(A, "P2", "FPS cap", "Set 20 fps then 60 fps", "Refresh rate follows the cap")
T(A, "P3", "Windows GPU preference button", "Click the Windows GPU preference button", "Confirmation; Windows Graphics settings list python.exe as High performance", "Windows only")
T(A, "P3", "Software-render hint", "Force `--cpu` on a machine with a GPU", "One-time dialog suggests switching to GPU; 'Don't show again' respected")

A = "Files & compatibility"
T(A, "P1", "Scenario round trip", "File > Save scenario; New; Open scenario", "Rocket, launch, plan and planet edits restored")
T(A, "P2", "Old/partial JSON", "Load a rocket JSON missing newer fields", "Loads with defaults; no crash")
T(A, "P1", "Invalid file handled", "Open a random .json / .txt as scenario", "Clear error message; app continues")
T(A, "P2", "Unicode paths", "Save/load files in a folder with spaces/accents", "Works")

A = "Scripting"
T(A, "P2", "Flight-computer example", "Flight computer > Enable script control (default script); Run", "Rocket follows the script; event log confirms")
T(A, "P2", "Script errors", "Enter invalid Python / no mission_loop; Enable", "Error logged; script disabled; app continues")
T(A, "P2", "Restricted builtins", "Add `import os` to the script", "Script rejected (imports blocked)")

A = "Multi-window"
T(A, "P2", "New 3D view", "Window > New 3D view window", "Floating view with own camera follows the simulation")
T(A, "P2", "New graph window", "Window > New graph window; change variable", "Live plot updates")
T(A, "P3", "Close all extra windows", "Window > Close all extra windows", "All extra windows close; main window unaffected")

A = "Robustness & performance"
T(A, "P1", "Rapid reset/run", "Press R and Space 20 times quickly", "No crash or hang")
T(A, "P2", "Resize during run", "Resize/maximise while running", "Rendering continues; no errors")
T(A, "P2", "Long run", "Run the Sun dive at 1000x for 10 minutes", "No memory growth beyond a few hundred MB; app responsive; status bar honest")
T(A, "P2", "Close while running", "Close the window during a run", "App exits cleanly within ~2 s; no zombie process")
T(A, "P2", "UI frame time", "Check 'UI xx ms' while running the LEO flight", "Below ~20 ms on a typical laptop in Quality mode")
T(A, "P2", "Frame back-pressure", "Run at 1000x and move the window", "UI stays responsive (no growing lag)")

A = "Documentation"
T(A, "P2", "Quick start works", "Follow docs/QUICKSTART.md exactly on a clean machine", "Every step works as written")
T(A, "P2", "Links valid", "Run `python tools/check_docs_links.py`", "0 broken links")
T(A, "P3", "Screenshots", "Run `python tools/check_screenshots.py`", "Lists placeholder vs real screenshots correctly")


def main():
    for i, c in enumerate(CASES, 1): c["id"] = f"TC-{i:03d}"
    areas = []
    for c in CASES:
        if c["area"] not in areas: areas.append(c["area"])
    md = ["# Manual test cases (generated)", "", f"**{len(CASES)} test cases** in {len(areas)} areas. Generated by `tools/gen_test_cases.py` - edit the data there, not this file. A CSV copy for test-management tools is in [test_cases.csv](test_cases.csv).", "",
          "**Priority:** P1 = must pass for a release, P2 = should pass, P3 = nice to have. **Result codes:** PASS · FAIL (file an issue) · BLOCKED · N/A.", "",
          "| Area | Cases | P1 |", "|---|---|---|"]
    for a in areas:
        cs = [c for c in CASES if c["area"] == a]; md.append(f"| {a} | {len(cs)} | {sum(1 for c in cs if c['pri'] == 'P1')} |")
    for a in areas:
        md += ["", f"## {a}", "", "| ID | Pri | Title | Steps | Expected result |", "|---|---|---|---|---|"]
        for c in [c for c in CASES if c["area"] == a]:
            steps = "<br>".join(f"{n}. {s}" for n, s in enumerate(c["steps"], 1)); md.append(f"| {c['id']} | {c['pri']} | **{c['title']}**<br><sub>{c['pre']}</sub> | {steps} | {c['expected']} |")
    md += ["", "## Result sheet template", "", "Copy into a *Test report* issue:", "", "```", "Build: ____  Date: ____  Tester: ____", "OS / Python / GPU: ____", "TC-001 PASS", "TC-002 PASS", "TC-003 FAIL  - short note (issue #__)", "...", "```", ""]
    os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, "MANUAL_TEST_CASES.md"), "w", encoding="utf-8").write("\n".join(md))
    with open(os.path.join(OUT, "test_cases.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["ID", "Area", "Priority", "Title", "Preconditions", "Steps", "Expected", "Result", "Notes"])
        for c in CASES: w.writerow([c["id"], c["area"], c["pri"], c["title"], c["pre"], " | ".join(f"{n}. {s}" for n, s in enumerate(c["steps"], 1)), c["expected"], "", ""])
    by = {c["title"]: c for c in CASES}
    SMOKE = ["Clean install from requirements", "Diagnostics report", "Animated splash", "Earth launch to LEO", "Live 3D preview", "Estimates update", "Default rocket passes", "Thin wall fails", "Abort",
             "Moon powered descent", "Porkchop computes", "Orbit change log", "Earth values", "Graph variables", "CSV export", "Renderer shown", "Scenario round trip", "Close while running"]
    sm = ["# Smoke test (10-15 minutes, generated)", "", "Run this on every release candidate and after any risky merge. If any step fails, stop and report - the build is not ready for wider testing.", "",
          "| # | Test case | Do | Expect | Result |", "|---|---|---|---|---|"]
    for i, t in enumerate(SMOKE, 1):
        c = by[t]; sm.append(f"| {i} | **{c['id']}** {c['title']} | {'; '.join(c['steps'])} | {c['expected']} | ☐ |")
    sm += ["", "Time box: 15 minutes. Record the environment (OS, Python, GPU, AstraX version) in the report.", ""]
    open(os.path.join(OUT, "SMOKE_TEST.md"), "w", encoding="utf-8").write("\n".join(sm))
    rg = ["# Regression checklist (generated)", "", "All **P1** cases, grouped by area. Run before every release and after changes to the matching area. Tick, then summarise in a *Test report* issue.", ""]
    for a in areas:
        cs = [c for c in CASES if c["area"] == a and c["pri"] == "P1"]
        if cs: rg += [f"## {a}", ""] + [f"- [ ] **{c['id']}** {c['title']} - {c['expected']}" for c in cs] + [""]
    rg += [f"Total P1 cases: {sum(1 for c in CASES if c['pri'] == 'P1')} of {len(CASES)}.", ""]
    open(os.path.join(OUT, "REGRESSION_CHECKLIST.md"), "w", encoding="utf-8").write("\n".join(rg))
    print(f"{len(CASES)} test cases in {len(areas)} areas; smoke {len(SMOKE)}; P1 {sum(1 for c in CASES if c['pri'] == 'P1')}")


if __name__ == "__main__":
    main()
