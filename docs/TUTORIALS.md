# Tutorials

Each tutorial lists **goal, steps, what you should see, what to try next**. Numbers are for the bundled demo rocket (illustrative, Falcon-class).

---
## 1. Reach orbit
**Goal** a stable ~200 km orbit.
1. Mission control ▸ *Earth launch to LEO* ▸ Load. Camera ▸ *Launch camera*. Press **Space**.
2. At ~150 s the first stage separates (white dot falls away); the upper stage inserts into orbit around T+450 s.
3. Open **Orbit analysis ▸ Orbit changes**: perigee climbs from negative (suborbital) to ~195 km.

**Expect** about 195 × 200 km, e ≈ 0.0003. **Try** change the pitch-kick in the preset (4° and 8° give different orbits; 10° fails).

## 2. Break a rocket on purpose
1. Rocket designer ▸ stage *Wall thickness* **0.5 mm** ▸ **Run survival test**.
2. Verdict: *VEHICLE LOST ... structural failure*. Click **Watch this launch in 3D** and see the breakup.
3. Now restore 4 mm and instead untick **Active attitude control** (the demo's centre of pressure is above its centre of mass) ▸ test again ▸ *loss of control*.
4. Set **Max dynamic pressure** to 15 kPa, untick *autopilot load protection* in the survival dialog ▸ *aerodynamic overload*.

**Learn** which limits bind: skin stress, max-Q, axial g, nose heating, attitude stability.

## 5-minute max-Q study
Designer ▸ example rocket ▸ run the survival test and read the margin table. Margins near 0 % are your design's weak spots. Then raise the limit being hit, or reduce the cause (more wall, fewer g, rounder nose).

---
## 3. Emergency abort
1. Load *Earth launch to LEO*, press **Space**, open **Flight safety**.
2. Watch the *Dynamic pressure* gauge. At about T+60 s press **ABORT**.
3. The stages fall away, the capsule coasts up, then a parachute opens below 7 km. Touchdown banner at ~7 m/s.

**Try** *Failure injection*: **Engine out**, **Propellant leak**, **Throttle stuck**, **Guidance lost**; then **Clear all faults**.
Also: Challenges ▸ **Abort at max-Q** ▸ Run.

## 4. Change an orbit
1. Start in orbit: Mission control ▸ start mode **orbit**, altitude 300 km ▸ Apply to simulation ▸ Run, pause.
2. **Orbit analysis ▸ Maneuver planner**: Prograde +100 m/s ▸ **Preview new orbit** (apogee rises), **Draw predicted path** (cyan ellipse in 3D).
3. **Apply impulse now** and watch the real orbit change.
4. **Hohmann helper**: target 1000 km ▸ *Compute* ▸ apply dv₁ ▸ coast to apogee ▸ apply dv₂.

**Rule** prograde raises the opposite side; normal burns change inclination; radial burns rotate the apsides.

## 5. Fly to the Sun
1. Mission control ▸ preset *LEO -> Sun dive* ▸ Load ▸ Run.
2. Telemetry ▸ **Trajectory & travel analysis** ▸ *Distance from Sun & destination vs time*.
3. The retrograde burn (7 km/s) lowers perihelion to ~0.34 AU. A real Sun impact needs ~24 km/s from LEO: more than this rocket can do.

## 6. Find an Earth → Mars launch window
1. Right panel ▸ **Launch windows**. From Earth to Mars, start 0 d, span 800 d, flight time 120–350 d ▸ **Compute**.
2. The porkchop plot shows total delta-v; the circle marks the best window (~day 469 ≈ April 2001, ~200 days, v∞ ≈ 3.5 km/s; this matches the real 2001 Mars Odyssey window).
3. **Fly best transfer in 3D**: the rocket starts on the departure leg; time runs at 2,000,000×.
4. Telemetry ▸ *distance to destination*: closest approach is ~1.9 million km. A real mission would add mid-course corrections.

**Try** Earth → Venus; widen the search span to see the ~26-month Mars cycle (synodic period 780 d).

## 7. Land on the Moon
1. Mission control ▸ preset **Moon powered descent (lunar lander)** ▸ Load (the lander replaces your rocket) ▸ Run.
2. The lander free-falls from 8 km, ignites a *suicide burn* ~2 km up, and touches down softly (propellant left ≈ 4.4 t).
3. Challenges ▸ **Moon soft landing** gives a verdict.

**Try** lowering propellant in the designer until the landing fails.

## 8. Study your design
Right panel ▸ **Studies**:
- **Max payload**: bisection for the biggest payload that still reaches orbit.
- **Parameter sweep**: e.g. `payload_mass_kg` from 2,000 to 14,000 in 8 steps → verdict, perigee, max-Q.
- **Monte Carlo**: ±3 % thrust, ±1 % Isp, ±10 % Cd... → success rate.
- **Re-entry**: capsule entry — peak g, heat flux, heat load, path.

## 9. Compare two designs
1. Run a design, Telemetry ▸ Graphs ▸ **Keep this run for comparison**.
2. Change the design, run again, tick both runs. Overlay graphs show the differences.
3. Export CSV or a Markdown mission report (File menu).

## 10. Multi-window setup
**Window ▸ New 3D view window** (launch camera) + **New graph window** (Mach) + main view (orbit camera on Earth). Drag them to a second monitor.
