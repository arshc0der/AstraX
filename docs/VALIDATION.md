# Validation (generated)

**69 tests.**

Every automated test, grouped by area. Run all of them with `python -m unittest discover -s tests -v`.

> Passing tests validate the **implementation against analytic/reference solutions**. They do not make AstraX a validated mission-analysis tool; see PHYSICS.md for the modelling limits.

## TestOrbital

| test | what it checks |
|---|---|
| `test_kepler_roundtrip` | kepler roundtrip |
| `test_hohmann_leo_geo` | textbook: dv_total ~ 3.89 km/s, tof ~ 5.28 h |
| `test_circular_period` | circular period |

## TestIntegrators

| test | what it checks |
|---|---|
| `test_rk4_order4` | rk4 order4 |
| `test_dopri_accuracy` | dopri accuracy |
| `test_verlet_energy_bounded` | verlet energy bounded |

## TestBodies

| test | what it checks |
|---|---|
| `test_reference_values` | reference values |
| `test_reset_and_modified` | reset and modified |
| `test_reference_not_mutated` | reference not mutated |
| `test_zero_momentum` | zero momentum |

## TestRocket

| test | what it checks |
|---|---|
| `test_tsiolkovsky_single_stage` | tsiolkovsky single stage |
| `test_twr` | twr |
| `test_json_roundtrip` | json roundtrip |
| `test_mesh_valid_and_responds` | mesh valid and responds |
| `test_obj_roundtrip` | obj roundtrip |
| `test_validation_flags_low_twr` | validation flags low twr |

## TestSimulation

| test | what it checks |
|---|---|
| `test_circular_orbit_stays_circular` | circular orbit stays circular |
| `test_nbody_energy_conserved` | nbody energy conserved |
| `test_earth_year` | Earth returns to ~same heliocentric longitude after one sidereal year |
| `test_changing_earth_mass_changes_orbit` | changing earth mass changes orbit |
| `test_free_fall_hits_surface` | free fall hits surface |
| `test_rocket_equation_in_simulation` | Vacuum, gravity-free-ish deep space burn: simulated dv must equal Isp*g0*ln(m0/m1). |
| `test_stability_warning` | stability warning |
| `test_atmosphere_density` | atmosphere density |
| `test_surface_launch_site_speed` | equatorial rotation speed ~ 465 m/s |
| `test_pad_hold_when_twr_low` | pad hold when twr low |
| `test_full_ascent_to_orbit` | integration test of the whole launch workflow |
| `test_scenario_roundtrip` | scenario roundtrip |

## TestRuntime

| test | what it checks |
|---|---|
| `test_script_controls_rocket_and_is_restricted` | script controls rocket and is restricted |
| `test_script_without_loop_rejected` | script without loop rejected |

## TestAeroAndSafety

| test | what it checks |
|---|---|
| `test_speed_of_sound_and_cd_curve` | speed of sound and cd curve |
| `test_sutton_graves_scaling` | sutton graves scaling |
| `test_shell_stress_hand_calc` | shell stress hand calc |
| `test_default_rocket_survives_ascent` | default rocket survives ascent |
| `test_survival_report_cases` | survival report cases |
| `test_overload_without_protection_destroys` | overload without protection destroys |
| `test_breakup_creates_debris_and_ends_run` | breakup creates debris and ends run |
| `test_engine_out_reduces_thrust` | engine out reduces thrust |
| `test_fuel_leak_loses_mass` | fuel leak loses mass |
| `test_abort_capsule_lands_safely` | abort capsule lands safely |
| `test_stage_debris_falls_back` | stage debris falls back |

## TestOrbitTools

| test | what it checks |
|---|---|
| `test_prograde_burn_matches_hohmann_apoapsis` | prograde burn matches hohmann apoapsis |
| `test_normal_burn_changes_inclination_only` | normal burn changes inclination only |
| `test_predict_returns_closed_orbit_without_touching_sim` | predict returns closed orbit without touching sim |
| `test_apply_impulse_changes_orbit` | apply impulse changes orbit |
| `test_orbit_log_recorded_on_events` | orbit log recorded on events |

## TestLambertAndTransfers

| test | what it checks |
|---|---|
| `test_lambert_curtis_example` | Curtis, Orbital Mechanics for Engineering Students, Example 5.2 |
| `test_lambert_solution_propagates_to_target` | lambert solution propagates to target |
| `test_synodic_period_earth_mars` | synodic period earth mars |
| `test_porkchop_finds_known_mars_window` | real 2001 Mars Odyssey: launched ~day 462 after J2000, ~200 d flight, C3 ~ 12 km2/s2 |
| `test_start_day_moves_planets` | start day moves planets |
| `test_transfer_start_preserves_v_infinity` | transfer start preserves v infinity |
| `test_lambert_transfer_flies_near_mars` | lambert transfer flies near mars |

## TestReentryLandingGroundTrack

| test | what it checks |
|---|---|
| `test_allen_eggers_peak_deceleration` | allen eggers peak deceleration |
| `test_earth_leo_entry_is_plausible` | earth leo entry is plausible |
| `test_hover_start_free_fall_time` | hover start free fall time |
| `test_powered_landing_is_soft` | powered landing is soft |
| `test_ground_track_at_pad_matches_launch_site` | ground track at pad matches launch site |
| `test_equatorial_launch_stays_on_equator_band` | equatorial launch stays on equator band |

## TestLibraryStudiesChallenges

| test | what it checks |
|---|---|
| `test_every_library_rocket_is_valid_and_builds` | every library rocket is valid and builds |
| `test_sounding_rocket_does_not_reach_orbit_and_ssto_fails` | sounding rocket does not reach orbit and ssto fails |
| `test_param_paths` | param paths |
| `test_sweep_payload_trend` | sweep payload trend |
| `test_monte_carlo_reproducible` | monte carlo reproducible |
| `test_challenges` | challenges |

## TestGpuSelection

| test | what it checks |
|---|---|
| `test_classify_gpu_names` | classify gpu names |
| `test_backend_choice` | backend choice |
| `test_lspci_parsing_dual_gpu_laptop` | lspci parsing dual gpu laptop |
| `test_software_renderer_detection` | software renderer detection |
