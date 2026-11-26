# Educators' guide

AstraX is designed to be used in classrooms, labs and clubs. All lessons run on student laptops (Python 3.10+) - no cloud, no accounts, no network.

## Learning outcomes covered
Newtonian gravity · orbital elements · Kepler's laws · the rocket equation and staging · thrust-to-weight · aerodynamic drag and max-Q · structural loads · Hohmann and Lambert transfers · launch windows · atmospheric re-entry · numerical integration and time-step stability · engineering design trade-offs and safety.

## Lesson plans (45–60 minutes each)
| # | Lesson | Activities | Tutorial |
|---|---|---|---|
| 1 | **How rockets reach orbit** | fly the preset; read Δv and T/W; plot altitude/velocity | Tutorial 1 |
| 2 | **The rocket equation** | change propellant/dry mass; predict Δv, verify in telemetry (*Learn ▸ Rocket equation*) | Learn tab |
| 3 | **Why multi-stage?** | compare single-stage (SSTO example) vs two-stage; use Studies ▸ Max payload | Tutorials 1, 8 |
| 4 | **Break it on purpose** | survival test with thin wall, no control, low max-Q limit | Tutorial 2 |
| 5 | **Changing orbits** | maneuver planner: raise apogee, change inclination, Hohmann | Tutorial 4 |
| 6 | **Orbital period and energy** | circular orbits at different altitudes; Kepler's third law from data | UI: Telemetry |
| 7 | **Going to Mars** | porkchop plot, synodic period, why windows repeat every ~26 months | Tutorial 6 |
| 8 | **Landing** | Moon landing; vary propellant; suicide burn concept | Tutorial 7 |
| 9 | **Numerics** | fixed dt vs auto; RK4 vs Verlet energy drift; read the warnings | Settings, toolbar |
| 10 | **Engineering report** | design a rocket for a payload; export a Markdown report; present margins | File ▸ Export report |

## Project ideas
- "Smallest rocket that reaches orbit with 100 kg" (Studies ▸ Max payload / sweeps).
- "Safest ascent": minimise max-Q and g while reaching orbit (sweep Cd, nose shape, limits).
- "Plan a mission to Venus/Jupiter": Launch windows, v∞ and C3 comparison.
- "Robustness study": Monte Carlo with different engine uncertainties; discuss margins.
- "Re-entry capsule design": compare ballistic coefficients with the Re-entry calculator.

## Assessment ideas
Rubric items: correct use of Δv budget · justified design limits · interpretation of margins · explanation of a failure (cause and fix) · validity discussion (what the model ignores - see [PHYSICS](PHYSICS.md)).

## Classroom tips
- Share rocket/scenario **JSON files** (Save design / Save scenario) so every student starts from the same state.
- Use *Settings ▸ Performance mode* on old laptops; *Window ▸ New 3D view* for a projector layout.
- Students can **record GIFs/MP4** of their launches (Record button).
- Always state the limitation: *results are simplified-model results, not validated mission predictions*.
- For advanced students: the engine is a plain Python package ([Scripting API](SCRIPTING_API.md)).

## Accessibility
All controls have tooltips; fonts scale (Settings); high-contrast theme available; colour is never the only signal for pass/fail (text verdicts included).

## Sharing your lesson
Open a pull request adding it to this page (CONTRIBUTING.md) - educators' contributions are very welcome.
