# AstraX physics model, assumptions and validation status

All internal units are SI (m, kg, s). Frame: barycentric ecliptic J2000 (inertial).

## Equations implemented
| Topic | Equation | Code |
|---|---|---|
| Gravity (N-body) | a_i = sum_j GM_j (r_j - r_i) / |r_j - r_i|^3 | `Simulation._body_acc` |
| Rocket equation | dv = Isp g0 ln(m0/mf); dm/dt = -F_vac/(Isp_vac g0) | `Rocket.estimates`, `Simulation` |
| Thrust vs pressure | F = mdot g0 Isp(p), Isp(p)=Isp_vac-(Isp_vac-Isp_sl) p/p0 | `_rocket_forces` |
| Drag | F = 1/2 rho Cd A v_air^2 (air co-rotates with body) | `_rocket_forces` |
| Kepler/elements | Newton solution of M = E - e sin E, state<->elements | `orbital.py` |
| Integrators | RK4, Dormand-Prince 5(4) adaptive, velocity Verlet | `integrators.py` |

## Aerodynamics, loads and failure model (v3.1)
| Topic | Model | Code |
|---|---|---|
| Speed of sound | a = sqrt(gamma R T); Earth T(h) from US-76 layers | `aero.py` |
| Drag | F = 1/2 rho Cd(M) A v^2, Cd(M) = Cd_ref x generic transonic curve (peak ~M 1.05) | `aero.cd_factor`, `Simulation._cd_area` |
| Lift / normal force | N = q A CN_alpha sin(a) cos(a); CN_alpha from simplified Barrowman | `aero.normal_force`, `Rocket.cn_alpha` |
| Heating | Sutton-Graves stagnation flux q = k sqrt(rho/Rn) v^3 | `aero.stagnation_heat_flux` |
| Structure | thin-tube stress sigma = N/(2 pi R t) + M/(pi R^2 t) at each stage base; failure at yield; design allowable = yield/FoS | `structure.py` |
| Load protection | autopilot throttles down (min 40 %) to keep g and max-Q under the limits | `Simulation.step` |
| Instability | uncontrolled vehicle with CoP above CoM: attitude error grows exponentially; loss of control above the AoA limit | `Simulation.step` |
| Breakup/impact | 45-50 fragments, ballistic with drag; jettisoned stages tracked as debris | `Simulation._explode`, `_step_debris` |
| Abort | stages jettisoned, +40 m/s kick, parachute (Cd 1.5) sized for 7 m/s touchdown, opens below 7 km | `Simulation.abort` |

**Not modelled:** buckling, fatigue, flutter, slosh, shock interaction, real-gas heating, wind, hold-down release dynamics, rotational attitude dynamics, engine-failure explosions, re-entry heating of a capsule.
All numeric limits and material values are order-of-magnitude placeholders you can edit; verify them for your vehicle.

## Orbit tools
`maneuver_preview` (elements before/after an ideal impulse), `predict` (coasts a deep copy of the simulation), `apply_impulse`, and an orbit log at every phase change / separation. Tested against Hohmann apoapsis, pure plane change at a node, and closed-orbit prediction.

## Data sources (see `astrax/bodies.py`)
GM and radii: JPL SSD "Planetary Physical Parameters"; Sun: IAU 2015 nominal. Orbital elements: E. M. Standish,
"Keplerian Elements for Approximate Positions of the Major Planets" (JPL, 1800-2050 table), epoch J2000.0.
Moon elements: approximate osculating values (Meeus). Earth air density: US Standard Atmosphere 1976 table.
**Please re-verify every number against the primary source before publishing.** Reference data is never modified;
edits live in a separate working copy and every body has a reset button.

## Known simplifications / limitations
* Mean Keplerian elements are not an ephemeris (arc-minute-level position errors for inner planets, worse for outer).
* Spin axis = ecliptic north tilted about +X by the axial tilt (true pole directions not used). No precession.
* Point-mass gravity (no J2/oblateness, no relativity). Rocket does not perturb bodies.
* Atmosphere: no weather/solar activity, constant Cd, no lift, no Mach/AoA dependence. Only Earth, Venus, Mars have atmospheres.
* Guidance/throttle/staging are evaluated once per step (zero-order hold). Attitude dynamics (rotation, TVC, moment of inertia) are
  **displayed/estimated but not simulated**: the vehicle points exactly where guidance commands.
* Center of pressure is a simplified Barrowman estimate; inertia assumes uniform cylinders.
* Phobos/Deimos, lift and rendezvous targeting tools are NOT implemented yet.

## Validation performed (`python -m unittest discover -s tests -v`, 46 tests)
* Kepler elements round-trip to 1e-9; Hohmann LEO->GEO dv/time match textbook values; circular-orbit period.
* RK4 shows order 4 convergence on a harmonic oscillator; Dormand-Prince < 1e-8 error; Verlet energy bounded.
* N-body total energy conserved to <1e-10 over 60 days (dt = 600 s); Earth returns to its starting longitude after one sidereal year (< 0.02 rad).
* Circular 400 km orbit stays circular (e < 1e-6, semi-major axis error < 1 m over 2 orbits) for rk4 / dopri5 / verlet.
* Simulated delta-v equals Tsiolkovsky prediction (1e-6 m/s) and propellant use equals mdot*t.
* Equatorial rotation speed at the launch site, US-76 densities, free fall -> crash, pad-hold when T/W < 1.
* Aerodynamics: speed of sound 340.3 / 295.1 m/s, Sutton-Graves ~v^3 and ~sqrt(rho), hand-calculated shell stress, transonic Cd peak.
* Safety: default rocket survives; 0.5 mm skin fails at liftoff; 1 engine cannot lift off; uncontrolled unstable design is lost; low q limit without protection is lost; breakup spawns debris; engine-out thrust x 8/9; fuel leak; abort lands the capsule at 7 m/s; stage debris impacts.
* Full ascent integration test: demo rocket reaches ~200 x 204 km orbit with `earth_leo()`.

NOT validated: absolute planetary positions vs JPL Horizons, drag/ascent against flight data, Max-Q realism (demo rocket is
illustrative, not an official vehicle model). Do **not** present results as research-grade predictions without your own validation.
