# AstraX User Guide

> Other documents: [QUICKSTART](QUICKSTART.md) · [TUTORIALS](TUTORIALS.md) · [UI_REFERENCE](UI_REFERENCE.md) · [FAQ](FAQ.md) · [index](README.md)

AstraX is a desktop laboratory where you **design a rocket, fly it in 3D, break it on purpose, and study what it did to the orbit**.
This guide is for normal users: no programming needed (except the optional flight-computer script).

> **Honest note:** AstraX is a learning and research-exploration tool. Its results are *simplified-model* results and are **not
> validated mission predictions**. See [PHYSICS.md](PHYSICS.md) for exactly what is modelled and what is not.

---

## 1. Install and start

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (Linux/macOS: source venv/bin/activate)
python -m pip install -r requirements.txt
python main.py
```

Optional: `pip install matplotlib` (PNG graphs inside reports) and install `ffmpeg` (MP4 recording; GIF works without it).

If a security policy blocks `pip.exe`, always use `python -m pip ...`.

---

## 2. The window at a glance

| Area | What it is for |
|---|---|
| **Centre tabs** | **Simulation** (3D view), **Rocket designer**, **Learn** (equations with live numbers) |
| **Left dock – Explorer** | Mission, rocket stages, celestial bodies. Double-click a body to focus the camera on it. |
| **Right dock** | **Mission control**, **Planet inspector**, **Flight safety**, **Orbit analysis** (tabs) |
| **Bottom dock** | **Telemetry & timeline** (live values, graphs, trajectory analysis) and **Event log** |
| **Top toolbar** | Run / Step / Stop / Reset / Stage, speed, integrator, timestep, camera, Record, Snapshot |
| **Status bar** | Simulation time, mission time, requested vs achieved speed, timestep, physics steps/s, FPS, numerics warnings |

Every dock can be **dragged, tabbed, floated, resized and closed**. *View ▸ Reset window layout* restores the default.

### Keyboard shortcuts
`Space` run/pause · `N` single step · `R` reset · `S` stage · `F` focus selected body · `Home` reset camera · `+` / `-` speed

---

## 3. Your first launch (2 minutes)

1. Open the **Simulation** tab. Right dock ▸ **Mission control** ▸ preset **“Earth launch to LEO”** ▸ *Load scenario preset*.
2. Press **Space** (or **Run**). Pick **Launch camera** in the toolbar camera box.
3. Watch: engine plume, liftoff, **banners** (LIFTOFF, STAGE SEPARATION …), the dropped first stage falling as white points, orbit insertion.
4. Open **Telemetry ▸ Graphs** for altitude, speed, Mach, heating, stress. Open **Orbit analysis** to see how each burn changed the orbit.

---

## 4. Build your own rocket

Open the **Rocket designer** tab.

### 4.1 Structure (left)
* **+ Stage** adds a core stage on top of the stack. **+ Booster** adds strap-on boosters beside the first stage (they burn in parallel and are dropped when empty).
* **Duplicate / Remove / Up / Down** edit the stack. Stage 1 is the bottom and launches first.

### 4.2 Properties (right)
| Group | You can edit |
|---|---|
| **Vehicle** | payload mass, drag coefficient, nose shape (ogive, conic, parabolic, elliptical, von Kármán), nose length and mass, nose-tip radius, **active attitude control** on/off |
| **Selected stage** | name, diameter, length, interstage, dry mass, fuel loaded, **max fuel capacity**, separation rule (burnout / time / manual), colour, **material and wall thickness** |
| **Engines** | number of engines, placement (single, ring, octaweb, cluster), thrust, Isp (vacuum and sea level), nozzle size. Fuel consumption is derived: *ṁ = F / (Isp·g₀)* |
| **Fins & legs** | fin count, span, chords; landing-leg count and length |
| **Design limits** | max dynamic pressure, max axial acceleration, max nose heat flux, factor of safety |

The 3D model rebuilds **live**. The table under the preview shows **ESTIMATES** (launch mass, mass ratio, thrust-to-weight, delta-v,
burn time, max acceleration, centre of mass/pressure, static margin, inertia). Estimates are analytic; **simulation results come only from running the simulation**.

### 4.3 Use your own 3D model
* **Import custom 3D model (OBJ)** – shows your mesh instead of the generated look (display only; physics uses your numbers).
* **Export rocket as OBJ** – open the generated rocket in Blender or any 3D tool.
* **Save / Load design (JSON)** – share designs with others.

### 4.4 “Will it survive?” – the survival test
Press **Will it survive? Run survival test…**

AstraX flies your design through a full Earth ascent (several pitch-kick angles), checking every step for:

| Failure | Meaning |
|---|---|
| **Aerodynamic overload** | dynamic pressure (max-Q) above 125 % of your limit |
| **Axial overload** | acceleration above 125 % of your limit |
| **Nose overheating** | stagnation heat flux above 125 % of your limit |
| **Structural failure** | skin stress (axial + bending) reaches the material’s yield |
| **Loss of control** | unstable design with active control switched off tumbles beyond the angle-of-attack limit |
| **Cannot lift off** | sea-level thrust-to-weight below 1 |

If it reaches orbit, AstraX coasts two orbits to check the orbit is stable. You get a **PASS/FAIL verdict**, a margin table
(peak vs limit), the timeline of events, and the trials tried. **Watch this launch in 3D** replays the best trial with the plume, staging debris and – if it fails – the breakup animation.

*Tips:* thin the wall to 0.5 mm and watch it break at liftoff; turn off *Active attitude control* on the default rocket (its centre of pressure is above the centre of mass) and watch it tumble; lower *Max dynamic pressure* below ~20 kPa and untick *autopilot protection* to trigger an aerodynamic breakup.

> A failure can reflect the generic ascent profile rather than your design. The report says so. This is a *screening* tool.

---

## 5. Flying: Mission control

### 5.1 Launch tab
Launch body and destination, start mode (**pad** or **parking orbit**), latitude/longitude, launch azimuth (0 = north, 90 = east), parking-orbit altitude, extra initial velocity.

### 5.2 Flight plan tab
A flight plan is a list of **phases**. A phase ends when *any* condition in its “Ends when” JSON is met.

| Mode | Behaviour |
|---|---|
| `fixed_local` | hold a pitch/heading in the local horizon frame (pitch 90 = straight up) |
| `pitch_program` | pitch follows a table over time |
| `gravity_turn` | follow the air-relative velocity (no angle of attack) |
| `ascent_hold` | closed-loop climb that steers to a target altitude and circularises |
| `prograde` / `retrograde` / `normal` / `antinormal` / `radial_out` / `radial_in` | burn along that direction relative to a reference body (`dominant`, `Sun`, or any body) |
| `coast` | engines off |

End conditions: `duration_s`, `dv_mps`, `altitude_m`, `speed_mps`, `apoapsis_alt_m`, `periapsis_alt_m`, `at_apoapsis`, `burnout`, `stages_jettisoned`.
Press **Apply to simulation** after editing.

### 5.3 Flight computer (Python)
Write `def mission_loop():` and use `rocket.set_thrust()`, `set_pitch()`, `set_heading()`, `get_altitude()`, `get_velocity()`, `stage()`, `log()`.
Scripts run with restricted builtins but are **not a security sandbox** – run only code you trust.

### 5.4 Presets
*Earth launch to LEO* · *LEO → Sun dive* (retrograde burn relative to the Sun) · *LEO → Mars transfer burn* (illustrative; launch windows are not modelled).

---

## 6. Time, accuracy and numerics
* **Speed box:** 0.1× … 1000× or **Custom**. Playback speed is *separate* from the physics timestep.
* **Integrator:** `rk4` (fixed step), `dopri5` (adaptive), `verlet` (symplectic – best for pure gravity coasts).
* **Timestep:** *auto* sizes dt from orbital and atmospheric resolution; *fixed* uses your value and shows **stability warnings** (e.g. “dt advances 0.68 rad of orbit per step”).
* If your computer cannot keep up, AstraX runs **slower than requested** and says so (requested vs achieved speed) – it never silently coarsens the physics.

---

## 7. Cameras and the 3D scene
* **Orbit, Free, Follow rocket, Follow selected body, First person, Launch camera** (pad scene, orbits around the rocket relative to the ground).
* **Top / Side / Front / Iso**, **Reset cam**, **Focus** (`F`).
* **View ▸ Visualisation layers:** planet orbits, rocket trajectory, velocity / acceleration / gravity vectors, atmosphere boundary, axes, labels, info overlay, grid. Each toggles independently.
* What you see: engine **plume** (length follows throttle), **launch pad**, **jettisoned stages** (white points), **explosion flash and fragments** on breakup or impact, **payload capsule** after an abort, **predicted orbit path** (cyan line, see §9).
* The rocket is drawn with a *visual scale* so it stays visible at planetary distances; the overlay shows the factor.

### Extra windows
**Window ▸ New 3D view window** opens another independent 3D view (e.g. launch camera in one, solar-system orbit view in another).
**Window ▸ New graph window** opens a floating live graph with any variable. Open as many as you like.

---

## 8. Flight safety and emergencies
Right dock ▸ **Flight safety**.

* **Load gauges** – dynamic pressure, axial g, nose heating, structural stress as a percentage of your design limits (green < 70 %, amber < 100 %, red ≥ 100 %).
* **ABORT** – cuts engines, jettisons every stage, kicks the payload capsule away and lowers it on a parachute sized for a ~7 m/s touchdown.
* **Engine cutoff**.
* **Failure injection** (what-if testing): engine out, propellant leak (kg/s), throttle stuck, guidance lost (attitude frozen), **Clear all faults**.
* **Realism options:** aerodynamics *advanced / simple*, **autopilot load protection** (throttles down for max-Q and g limits, minimum 40 %), and whether failures destroy the vehicle.

Events appear as on-screen **banners** and in the **Event log**; warnings fire once when a load exceeds its limit.

---

## 9. Orbit analysis – how did my burn change the orbit?
Right dock ▸ **Orbit analysis**.

* **Orbit changes** – a table of the orbit (perigee, apogee, eccentricity, inclination, speed) at **every phase change and stage separation**, plus a live perigee/apogee graph.
* **Maneuver planner** – enter prograde / normal / radial delta-v, then:
  * **Preview new orbit** – before/after elements (no change to the simulation).
  * **Draw predicted path** – coasts a *copy* of the simulation and draws the future orbit in 3D.
  * **Apply impulse now** – ideal instantaneous burn (what-if; uses no propellant).
  * **Hohmann helper** – computes dv₁, dv₂ and transfer time to a target altitude.
* Rule of thumb: prograde raises the *opposite* side of the orbit, normal burns rotate the orbital plane, radial burns rotate the line of apsides.

---

## 10. Planets and the solar system
**Planet inspector** lists the Sun, Mercury … Neptune and the Moon. Edit mass, radius, rotation, axial tilt and orbital elements.
Editing restarts the simulation so gravity and motion use the new values. **Reset to default** restores one body; **Reset ALL** restores everything. Edited bodies are flagged **MODIFIED**. Sources, epoch and limitations are shown for each body. Save/load planet configurations as JSON.

---

## 11. Telemetry, data and reports
* **Live** tab – readouts incl. Mach, angle of attack, heat flux, stress, faults.
* **Graphs** tab – four graphs with selectable variables (units on every axis), **Keep this run for comparison**, overlay several runs, zoom/pan.
* **Trajectory & travel analysis** – relative orbit, heliocentric path, or distance-to-Sun / distance-to-destination vs time, with closest approach and a naïve ETA. Use this for “rocket heading to the Sun or a planet”.
* **Export:** CSV (units in headers), JSON sessions (save/load/compare), Markdown mission report (+ PNG graphs if matplotlib is installed, estimates and results in separate sections), scenarios, rocket designs.
* **Logs:** `logs/astrax_<timestamp>.log` (*Tools ▸ Open logs folder*).
* **Recording:** toolbar **Record** → GIF (or MP4 with ffmpeg). **Snapshot** saves a PNG.

---

## 12. Customise AstraX
**Tools ▸ Settings & customisation…**: colour theme (*Mission control dark, Midnight blue, High contrast, Light*), interface font size, trail length, planet size exaggeration, plume on/off, telemetry sample interval. Settings are remembered.

---

## 12b. New in 3.2: planning, landing, studies, challenges

### Launch windows (right panel ▸ *Launch windows*)
Choose origin and destination planets, a search start (days after J2000), span, and flight-time range, then **Compute**. AstraX solves Lambert's problem for a grid of departure dates and flight times and draws a **porkchop plot** (total delta-v). The best window is summarised (dates, v-infinity, C3, burns, synodic period). **Fly best transfer in 3D** starts the rocket on the hyperbolic departure leg at the right epoch and runs the N-body simulation at 2,000,000x; watch *distance to destination* in Telemetry. Validated against the real 2001 Mars Odyssey window. Mean-element model: dates are indicative.

### Powered landing and hover starts
Start mode **hover** places the rocket at rest above the surface; the flight-plan mode `powered_landing` performs a suicide-burn landing (retrograde burn timed so deceleration reaches ~85 % of available, then a descent-rate controller near the ground). Preset **Moon powered descent** loads the *Lunar lander* example rocket.

### Example rockets
Designer ▸ *Example rockets*: Falcon-class two-stage, small launcher, heavy lifter with boosters, sounding rocket (suborbital), SSTO attempt (cannot reach orbit), lunar lander. All numbers are illustrative.

### Studies
*Max payload* (bisection), *Parameter sweep* (any rocket field by path, e.g. `stages[0].engine.count`), *Monte Carlo* (random thrust/Isp/Cd/mass errors → success rate), *Re-entry calculator* (peak g, heat flux, heat load; validated against Allen-Eggers).

### Challenges
First orbit, Gentle ascent (max-Q under 30 kPa), Moon soft landing, Abort at max-Q. *Run* gives a headless pass/fail with a message; *Load in 3D* sets up the scenario for you to fly.

### Ground track
Telemetry ▸ Trajectory ▸ *Ground track* plots the sub-point latitude/longitude on the dominant body.

### Look and feel
The splash screen plays your logo animation on the theme colour; the window uses a dark Fusion palette and (on Windows) a dark native title bar matching the theme. Change it in *Settings*. See [BRANDING](BRANDING.md).

---

## 13. Troubleshooting

| Problem | What to do |
|---|---|
| `pip.exe` blocked | Use `python -m pip install -r requirements.txt` |
| “DLL load failed … Application Control” | Your PC’s security policy blocked a Qt DLL; retry, or ask your IT admin |
| Window larger than screen | Use *View ▸ Reset window layout*; panels scroll when space is tight |
| Run is slower than requested | CPU limit; see status bar. Lower the speed or use `verlet`/larger *auto* dt |
| “dt too large” warning | Switch dt mode to **auto** or reduce dt |
| Test your install without the GUI | `python -m unittest discover -s tests -v` |

Please report bugs with the full terminal text and, if possible, a screenshot.

---

## 14. Glossary
**Delta-v** change in velocity a rocket can produce · **Isp** engine efficiency (seconds) · **T/W** thrust-to-weight ratio · **Max-Q** peak dynamic pressure q = ½ρv² ·
**Mach** speed ÷ speed of sound · **Angle of attack** angle between the rocket axis and the airflow · **CoM / CoP** centres of mass / pressure (CoP below CoM = stable) ·
**Perigee / apogee** lowest / highest point of an orbit · **Prograde** along the velocity.
