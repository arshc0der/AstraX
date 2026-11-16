"""Save / load rockets, planet configurations, full mission scenarios (readable JSON)."""
from __future__ import annotations
import json, dataclasses
from .rocket import Rocket
from .bodies import SolarSystem, Body, Atmosphere, REFERENCE_BODIES
from .simulation import LaunchConfig, Phase, SimConfig

EDITABLE_FIELDS = ("gm", "radius_m", "rotation_period_s", "axial_tilt_deg", "a", "e", "inc", "raan", "argp", "m0")


def planets_to_dict(system: SolarSystem, only_modified=False) -> dict:
    out = {}
    for b in system.bodies:
        if only_modified and not system.is_modified(b.name): continue
        d = {k: getattr(b, k) for k in EDITABLE_FIELDS}
        if b.atmosphere: d["atmosphere"] = dataclasses.asdict(b.atmosphere)
        out[b.name] = d
    return out


def apply_planets(system: SolarSystem, d: dict):
    for name, vals in d.items():
        b = system.get(name)
        for k, v in vals.items():
            if k == "atmosphere" and b.atmosphere is not None: b.atmosphere = Atmosphere(**v)
            elif k in EDITABLE_FIELDS: setattr(b, k, v)


def save_scenario(path, rocket, launch, plan, config, system=None, name="Scenario"):
    data = {"astrax_format": "scenario/1", "name": name, "rocket": rocket.to_dict(),
            "launch": dataclasses.asdict(launch), "plan": [dataclasses.asdict(p) for p in plan],
            "sim_config": dataclasses.asdict(config),
            "planet_overrides": planets_to_dict(system, only_modified=True) if system else {}}
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2)


def load_scenario(path):
    with open(path, encoding="utf-8") as f: d = json.load(f)
    if d.get("astrax_format") != "scenario/1": raise ValueError("Not an AstraX scenario file")
    rocket = Rocket.from_dict(d["rocket"])
    ld = d["launch"]; ld["extra_velocity_mps"] = tuple(ld.get("extra_velocity_mps", (0, 0, 0)))
    launch = LaunchConfig(**ld); plan = [Phase(**p) for p in d["plan"]]; cfg = SimConfig(**d["sim_config"])
    system = SolarSystem(); apply_planets(system, d.get("planet_overrides", {}))
    return rocket, launch, plan, cfg, system, d.get("name", "Scenario")
