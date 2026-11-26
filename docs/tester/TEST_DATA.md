# Test data and expected values

Use these to judge whether a result is plausible. Values come from the automated tests and validation runs (tolerances in [VALIDATION](../VALIDATION.md)).

## Reference results
| Scenario | Expected |
|---|---|
| *Earth launch to LEO*, demo rocket | orbit ≈ **195 × 200 km**, e ≈ 0.0003; stage 1 separation ≈ **T+147 s**; insertion burn ends ≈ T+450 s; peak axial load ≈ 5.7 g with protection |
| Survival test, demo rocket | **PASS**, stable ≈ 199 × 304 km orbit |
| Wall thickness 0.5 mm (all stages) | LOST **T+1 s**, structural (skin stress ≈ 1280 MPa vs yield 450 MPa) |
| Active control off (demo rocket) | LOST, loss of control (angle of attack ≈ 25° near T+218 s) |
| Engine count 1 on stage 1 | NO_LIFTOFF (T/W ≈ 0.16 at that setting; < 1) |
| Abort near max-Q (~T+62 s) | capsule LANDED at **7.0 m/s** with parachute |
| Moon descent from 8 km (lander) | LANDING BURN ≈ 2.4 km altitude; LANDED < 10 m/s; ≈ 4,400 kg propellant left |
| Earth → Mars porkchop (start 0, span 800, 120–350 d) | best window ≈ **day 469 (April 2001)**, flight ≈ **199 d**, v∞ ≈ **3.47 km/s**, C3 ≈ 12 km²/s², total Δv ≈ 6.3 km/s (300 km orbits) |
| Synodic period Earth–Mars | **779.9 d** |
| Mars transfer flight (N-body) | closest approach to Mars ≈ **1.9×10⁹ m** at day ≈ 185 |
| LEO → Sun dive preset (7 km/s retrograde) | perihelion ≈ **0.34 AU** at ≈ day 117 |
| Re-entry: 5000 kg, Cd 1.3, A 12 m², Rn 4.7 m, 7800 m/s, 2° | peak ≈ **8.8 g** at ≈ 39 km, flux ≈ 560 kW/m², load ≈ 66 MJ/m² |
| 400 km circular orbit | period ≈ **92.4 min** (5545 s), speed ≈ 7.67 km/s |
| LEO→GEO Hohmann | Δv ≈ 3.9 km/s, flight ≈ 5.28 h |
| Earth (inspector) | g ≈ 9.82 m/s², density ≈ 5514 kg/m³, orbital period ≈ 365.25 d |
| Equatorial surface speed (Earth rotation) | ≈ 465 m/s |

## Handy constants
G = 6.67430×10⁻¹¹ · AU = 1.495978707×10¹¹ m · g₀ = 9.80665 m/s² · Earth GM = 3.986004418×10¹⁴ m³/s² · Sun GM = 1.32712440018×10²⁰ m³/s² · Moon g ≈ 1.62 m/s².

## Files for testing
- Rockets: *Designer ▸ Example rockets* + Save design.
- Scenarios: *File ▸ Save scenario* after loading each preset.
- Sessions: *Telemetry ▸ Save session* after the LEO flight.
Attach failing files to issues.
