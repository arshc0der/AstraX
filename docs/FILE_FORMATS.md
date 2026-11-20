# File formats (generated)

All files are UTF-8 JSON, human-readable, and carry an `astrax_format` tag. Unknown/missing fields fall back to the defaults below, so older files keep loading.

| Format tag | Written by | Contains |
|---|---|---|
| `rocket/1` | Rocket designer > Save design | one rocket |
| `scenario/1` | File > Save scenario | rocket + launch + flight plan + sim config + planet overrides |
| `planets/1` | Planet inspector > Save | edited planet parameters |
| `session/1` | Telemetry > Save session | recorded telemetry arrays, events, units |
| `.csv` | Telemetry > Export CSV | one row per sample, units in the headers |

## Rocket

Rocket(name: 'str' = 'Custom Rocket', stages: 'list' = <factory>, payload_mass_kg: 'float' = 1000.0, nose: 'Nose' = <factory>, cd: 'float' = 0.35, custom_mesh_path: 'str' = '', nose_radius_m: 'float' = 0.3, intended_body: 'str' = 'Earth', active_control: 'bool' = True, limits: 'Limits' = <factory>, notes: 'str' = '')

| field | type | default |
|---|---|---|
| `name` | `str` | `Custom Rocket` |
| `stages` | `list` | `(factory)` |
| `payload_mass_kg` | `float` | `1000.0` |
| `nose` | `Nose` | `(factory)` |
| `cd` | `float` | `0.35` |
| `custom_mesh_path` | `str` | `` |
| `nose_radius_m` | `float` | `0.3` |
| `intended_body` | `str` | `Earth` |
| `active_control` | `bool` | `True` |
| `limits` | `Limits` | `(factory)` |
| `notes` | `str` | `` |

## Stage

Stage(name: 'str' = 'Stage', kind: 'str' = 'core', diameter_m: 'float' = 3.0, length_m: 'float' = 20.0, dry_mass_kg: 'float' = 5000.0, propellant_kg: 'float' = 50000.0, propellant_capacity_kg: 'float' = 0.0, engine: 'Engine' = <factory>, interstage_length_m: 'float' = 0.8, fin_count: 'int' = 0, fin_span_m: 'float' = 1.5, fin_root_chord_m: 'float' = 2.5, fin_tip_chord_m: 'float' = 1.0, leg_count: 'int' = 0, leg_length_m: 'float' = 6.0, separation: 'str' = 'burnout', separation_time_s: 'float' = 0.0, tank_split: 'bool' = True, color: 'tuple' = (0.92, 0.92, 0.95, 1.0), booster_count: 'int' = 1, cd: 'float' = 0.0, material: 'str' = 'Al-Li 2195', wall_thickness_mm: 'float' = 4.0)

| field | type | default |
|---|---|---|
| `name` | `str` | `Stage` |
| `kind` | `str` | `core` |
| `diameter_m` | `float` | `3.0` |
| `length_m` | `float` | `20.0` |
| `dry_mass_kg` | `float` | `5000.0` |
| `propellant_kg` | `float` | `50000.0` |
| `propellant_capacity_kg` | `float` | `0.0` |
| `engine` | `Engine` | `(factory)` |
| `interstage_length_m` | `float` | `0.8` |
| `fin_count` | `int` | `0` |
| `fin_span_m` | `float` | `1.5` |
| `fin_root_chord_m` | `float` | `2.5` |
| `fin_tip_chord_m` | `float` | `1.0` |
| `leg_count` | `int` | `0` |
| `leg_length_m` | `float` | `6.0` |
| `separation` | `str` | `burnout` |
| `separation_time_s` | `float` | `0.0` |
| `tank_split` | `bool` | `True` |
| `color` | `tuple` | `(0.92, 0.92, 0.95, 1.0)` |
| `booster_count` | `int` | `1` |
| `cd` | `float` | `0.0` |
| `material` | `str` | `Al-Li 2195` |
| `wall_thickness_mm` | `float` | `4.0` |

## Engine

Engine(count: 'int' = 1, thrust_vac_n: 'float' = 100000.0, isp_vac_s: 'float' = 300.0, isp_sl_s: 'float' = 270.0, nozzle_diameter_m: 'float' = 0.8, nozzle_length_m: 'float' = 1.2, placement: 'str' = 'single', gimbal_deg: 'float' = 5.0)

| field | type | default |
|---|---|---|
| `count` | `int` | `1` |
| `thrust_vac_n` | `float` | `100000.0` |
| `isp_vac_s` | `float` | `300.0` |
| `isp_sl_s` | `float` | `270.0` |
| `nozzle_diameter_m` | `float` | `0.8` |
| `nozzle_length_m` | `float` | `1.2` |
| `placement` | `str` | `single` |
| `gimbal_deg` | `float` | `5.0` |

## Nose

Nose(shape: 'str' = 'ogive', length_m: 'float' = 6.0, base_diameter_m: 'float' = 3.0, mass_kg: 'float' = 0.0, color: 'tuple' = (0.95, 0.95, 0.98, 1.0))

| field | type | default |
|---|---|---|
| `shape` | `str` | `ogive` |
| `length_m` | `float` | `6.0` |
| `base_diameter_m` | `float` | `3.0` |
| `mass_kg` | `float` | `0.0` |
| `color` | `tuple` | `(0.95, 0.95, 0.98, 1.0)` |

## Limits

Design limits. 'limit' = design allowable; failure happens at limit * fail_factor (or sigma >= yield).

| field | type | default |
|---|---|---|
| `max_q_pa` | `float` | `60000.0` |
| `max_axial_g` | `float` | `6.0` |
| `max_heat_flux_w_m2` | `float` | `1000000.0` |
| `factor_of_safety` | `float` | `1.4` |
| `fail_factor` | `float` | `1.25` |
| `max_aoa_deg` | `float` | `25.0` |

## LaunchConfig

LaunchConfig(body: 'str' = 'Earth', lat_deg: 'float' = 28.5, lon_deg: 'float' = -80.6, site_altitude_m: 'float' = 0.0, start_mode: 'str' = 'pad', start_day: 'float' = 0.0, orbit_altitude_m: 'float' = 300000.0, heading_deg: 'float' = 90.0, target_body: 'str' = 'Moon', extra_velocity_mps: 'tuple' = (0.0, 0.0, 0.0))

| field | type | default |
|---|---|---|
| `body` | `str` | `Earth` |
| `lat_deg` | `float` | `28.5` |
| `lon_deg` | `float` | `-80.6` |
| `site_altitude_m` | `float` | `0.0` |
| `start_mode` | `str` | `pad` |
| `start_day` | `float` | `0.0` |
| `orbit_altitude_m` | `float` | `300000.0` |
| `heading_deg` | `float` | `90.0` |
| `target_body` | `str` | `Moon` |
| `extra_velocity_mps` | `tuple` | `(0.0, 0.0, 0.0)` |

## Phase

One segment of the flight plan. The phase ends when ANY `until` condition is met.

| field | type | default |
|---|---|---|
| `name` | `str` | `Phase` |
| `mode` | `str` | `hold` |
| `throttle` | `float` | `1.0` |
| `pitch_deg` | `float` | `90.0` |
| `heading_deg` | `float` | `90.0` |
| `pitch_table` | `list` | `(factory)` |
| `ref` | `str` | `dominant` |
| `target_alt_m` | `float` | `0.0` |
| `until` | `dict` | `(factory)` |
| `q_limit_pa` | `float` | `0.0` |

## SimConfig

SimConfig(method: 'str' = 'rk4', dt_mode: 'str' = 'fixed', dt_s: 'float' = 0.05, dt_min_s: 'float' = 0.005, dt_max_s: 'float' = 600.0, rtol: 'float' = 1e-10, landing_speed_mps: 'float' = 10.0, record_interval_s: 'float' = 1.0, aero: 'str' = 'advanced', protect: 'bool' = True, failures: 'bool' = True, post_failure_s: 'float' = 120.0)

| field | type | default |
|---|---|---|
| `method` | `str` | `rk4` |
| `dt_mode` | `str` | `fixed` |
| `dt_s` | `float` | `0.05` |
| `dt_min_s` | `float` | `0.005` |
| `dt_max_s` | `float` | `600.0` |
| `rtol` | `float` | `1e-10` |
| `landing_speed_mps` | `float` | `10.0` |
| `record_interval_s` | `float` | `1.0` |
| `aero` | `str` | `advanced` |
| `protect` | `bool` | `True` |
| `failures` | `bool` | `True` |
| `post_failure_s` | `float` | `120.0` |

## Example: rocket file (first stage only)

```json
{
  "astrax_format": "rocket/1",
  "name": "Falcon-class demo (illustrative)",
  "stages": [
    {
      "name": "Stage 1",
      "kind": "core",
      "diameter_m": 3.7,
      "length_m": 42.0,
      "dry_mass_kg": 25600,
      "propellant_kg": 395700,
      "propellant_capacity_kg": 0,
      "engine": {
        "count": 9,
        "thrust_vac_n": 914000.0,
        "isp_vac_s": 311,
        "isp_sl_s": 282,
        "nozzle_diameter_m": 1.0,
        "nozzle_length_m": 1.4,
        "placement": "octaweb",
        "gimbal_deg": 5
      },
      "interstage_length_m": 1.0,
      "fin_count": 4,
      "fin_span_m": 1.8,
      "fin_root_chord_m": 2.8,
      "fin_tip_chord_m": 1.0,
      "leg_count": 4,
      "leg_length_m": 7.0,
      "separation": "burnout",
      "separation_time_s": 0.0,
      "tank_split": true,
      "color": [
        0.92,
        0.92,
        0.95,
        1.0
      ],
      "booster_count": 1,
      "cd": 0.0,
      "material": "Al-Li 2195",
      "wall_thickness_mm": 4.0
    }
  ],
  "payload_mass_kg": 10000.0,
  "nose": {
    "shape": "ogive",
    "length_m": 6.0,
    "base_diameter_m": 3.7,
    "mass_kg": 1500.0,
    "color": [
      0.95,
      0.95,
      0.98,
      1.0
    ]
  },
  "cd": 0.3,
  "custom_mesh_path": "",
  "nose_radius_m": 0.3,
  "intended_body": "Earth",
  "active_control": true,
  "limits": {
    "max_q_pa": 60000.0,
    "max_axial_g": 6.0,
    "max_heat_flux_w_m2": 1000000.0,
    "factor_of_safety": 1.4,
    "fail_factor": 1.25,
    "max_aoa_deg": 25.0
  },
  "notes": ""
}
```

## Example: flight plan

```json
[
  {
    "name": "Vertical rise",
    "mode": "fixed_local",
    "throttle": 1.0,
    "pitch_deg": 90,
    "heading_deg": 90,
    "pitch_table": [],
    "ref": "dominant",
    "target_alt_m": 0.0,
    "until": {
      "duration_s": 10
    },
    "q_limit_pa": 0.0
  },
  {
    "name": "Pitch kick",
    "mode": "pitch_program",
    "throttle": 1.0,
    "pitch_deg": 90,
    "heading_deg": 90,
    "pitch_table": [
      [
        0,
        90
      ],
      [
        6,
        84.0
      ]
    ],
    "ref": "dominant",
    "target_alt_m": 0.0,
    "until": {
      "duration_s": 6
    },
    "q_limit_pa": 0.0
  },
  {
    "name": "Gravity turn (stage 1)",
    "mode": "gravity_turn",
    "throttle": 1.0,
    "pitch_deg": 90.0,
    "heading_deg": 90.0,
    "pitch_table": [],
    "ref": "dominant",
    "target_alt_m": 0.0,
    "until": {
      "stages_jettisoned": 1
    },
    "q_limit_pa": 0.0
  },
  {
    "name": "Orbit insertion burn",
    "mode": "ascent_hold",
    "throttle": 1.0,
    "pitch_deg": 90.0,
    "heading_deg": 90.0,
    "pitch_table": [],
    "ref": "dominant",
    "target_alt_m": 200000.0,
    "until": {
      "periapsis_alt_m": 194000.0
    },
    "q_limit_pa": 0.0
  },
  {
    "name": "Parked in orbit",
    "mode": "coast",
    "throttle": 0.0,
    "pitch_deg": 90.0,
    "heading_deg": 90.0,
    "pitch_table": [],
    "ref": "dominant",
    "target_alt_m": 0.0,
    "until": {},
    "q_limit_pa": 0.0
  }
]
```

## Flight-plan modes and end conditions

Modes: `fixed_local`, `pitch_program`, `gravity_turn`, `ascent_hold`, `powered_landing`, `prograde`, `retrograde`, `normal`, `antinormal`, `radial_out`, `radial_in`, `coast`, `hold`.

End conditions (`until`, any satisfied ends the phase): `duration_s`, `dv_mps`, `altitude_m`, `speed_mps`, `apoapsis_alt_m`, `periapsis_alt_m`, `at_apoapsis`, `burnout`, `stages_jettisoned`.

Start modes (`LaunchConfig.start_mode`): `pad`, `orbit`, `hover`, `transfer`.
