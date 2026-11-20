"""Example rockets. ALL numbers are rough, illustrative, publicly-quoted orders of magnitude - NOT official vehicle models."""
from __future__ import annotations
from .rocket import Rocket, Stage, Engine, Nose, default_rocket


def small_launcher():
    s1 = Stage(name="Stage 1", diameter_m=1.2, length_m=12.0, dry_mass_kg=950, propellant_kg=9250, engine=Engine(9, 25e3, 311, 280, 0.35, 0.5, "octaweb"), interstage_length_m=0.3, wall_thickness_mm=2.0)
    s2 = Stage(name="Stage 2", diameter_m=1.2, length_m=4.0, dry_mass_kg=250, propellant_kg=2050, engine=Engine(1, 26e3, 343, 300, 0.8, 1.2, "single"), interstage_length_m=0.2, wall_thickness_mm=2.0)
    return Rocket("Small launcher (Electron-class, illustrative)", [s1, s2], 150.0, Nose("ogive", 2.0, 1.2, 40.0), 0.30, nose_radius_m=0.15)


def heavy_with_boosters():
    core = Stage(name="Core", diameter_m=3.7, length_m=40.0, dry_mass_kg=22000, propellant_kg=380000, engine=Engine(9, 914e3, 311, 282, 1.0, 1.4, "octaweb"), wall_thickness_mm=4.5)
    boost = Stage(name="Side booster", kind="booster", diameter_m=3.7, length_m=40.0, dry_mass_kg=22000, propellant_kg=380000, engine=Engine(9, 914e3, 311, 282, 1.0, 1.4, "octaweb"), booster_count=2, wall_thickness_mm=4.5)
    up = Stage(name="Upper stage", diameter_m=3.7, length_m=12.0, dry_mass_kg=4000, propellant_kg=92670, engine=Engine(1, 934e3, 348, 311, 2.4, 3.0, "single"), interstage_length_m=0.5, wall_thickness_mm=4.0)
    return Rocket("Heavy lifter with side boosters (illustrative)", [boost, core, up], 25000.0, Nose("ogive", 7.0, 3.7, 2500.0), 0.32)


def sounding_rocket():
    s = Stage(name="Motor", diameter_m=0.3, length_m=4.5, dry_mass_kg=110, propellant_kg=420, engine=Engine(1, 14e3, 250, 225, 0.25, 0.4, "single"), fin_count=4, fin_span_m=0.35, fin_root_chord_m=0.7, fin_tip_chord_m=0.3, wall_thickness_mm=2.0)
    return Rocket("Sounding rocket (suborbital)", [s], 30.0, Nose("von_karman", 0.9, 0.3, 5.0), 0.40, nose_radius_m=0.03)


def ssto_attempt():
    s = Stage(name="SSTO", diameter_m=5.0, length_m=35.0, dry_mass_kg=14000, propellant_kg=86000, engine=Engine(3, 700e3, 440, 360, 1.6, 2.2, "ring"), wall_thickness_mm=4.0, leg_count=4)
    return Rocket("SSTO attempt (cannot reach orbit)", [s], 1000.0, Nose("ogive", 6.0, 5.0, 800.0), 0.35)


def lunar_lander():
    s = Stage(name="Descent stage", diameter_m=3.2, length_m=3.0, dry_mass_kg=2200, propellant_kg=5000, engine=Engine(1, 30e3, 311, 311, 0.9, 1.3, "single"), leg_count=4, leg_length_m=3.0, wall_thickness_mm=2.0, interstage_length_m=0.2)
    return Rocket("Lunar lander (Moon only)", [s], 500.0, Nose("conic", 1.2, 3.2, 100.0), 0.5, intended_body="Moon", active_control=True)


LIBRARY = {
    "Falcon-class 2-stage (default)": default_rocket,
    "Small launcher (Electron-class)": small_launcher,
    "Heavy lifter with side boosters": heavy_with_boosters,
    "Sounding rocket (suborbital)": sounding_rocket,
    "SSTO attempt (cannot reach orbit)": ssto_attempt,
    "Lunar lander (Moon only)": lunar_lander,
}


def get_rocket(name: str) -> Rocket:
    return LIBRARY[name]()
