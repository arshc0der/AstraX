"""Mission scenario presets: (LaunchConfig, flight plan). Tuned for the bundled demo rocket; adjust for others.

Every preset is plain data (Phase dataclasses) so users can copy, edit and save them as JSON.
"""
from __future__ import annotations
from .simulation import LaunchConfig, Phase


def earth_leo(target_alt_m=200e3, kick_deg=6.0):
    """Two-stage ascent: vertical -> pitch kick -> gravity turn to stage-1 burnout -> closed-loop
    altitude-hold insertion burn (mode 'ascent_hold') until the periapsis reaches the target."""
    L = LaunchConfig(body="Earth", lat_deg=28.5, lon_deg=-80.6, heading_deg=90.0, target_body="Moon")
    plan = [
        Phase("Vertical rise", "fixed_local", 1.0, 90, 90, until={"duration_s": 10}),
        Phase("Pitch kick", "pitch_program", 1.0, 90, 90, [[0, 90], [6, 90 - kick_deg]], until={"duration_s": 6}),
        Phase("Gravity turn (stage 1)", "gravity_turn", 1.0, until={"stages_jettisoned": 1}),
        Phase("Orbit insertion burn", "ascent_hold", 1.0, target_alt_m=target_alt_m,
              until={"periapsis_alt_m": target_alt_m * 0.97}),
        Phase("Parked in orbit", "coast", 0.0, until={}),
    ]
    return L, plan


def leo_to_sun_dive(alt_m=300e3, dv_mps=7000.0):
    """Start in LEO, burn retrograde relative to the Sun to lower perihelion (heliocentric reference)."""
    L = LaunchConfig(body="Earth", start_mode="orbit", orbit_altitude_m=alt_m, heading_deg=90, target_body="Sun")
    plan = [Phase("Coast to departure point", "coast", 0.0, until={"duration_s": 60}),
            Phase("Escape + retrograde (Sun ref.)", "retrograde", 1.0, ref="Sun", until={"dv_mps": dv_mps}),
            Phase("Coast", "coast", 0.0, until={})]
    return L, plan


def leo_to_mars_transfer(alt_m=300e3, dv_mps=3600.0):
    L = LaunchConfig(body="Earth", start_mode="orbit", orbit_altitude_m=alt_m, heading_deg=90, target_body="Mars")
    plan = [Phase("Coast", "coast", 0.0, until={"duration_s": 60}),
            Phase("Trans-Mars injection", "prograde", 1.0, ref="dominant", until={"dv_mps": dv_mps}),
            Phase("Coast", "coast", 0.0, until={})]
    return L, plan


def moon_descent(alt_m=8000.0):
    """Hover start at rest above the Moon, then an automatic suicide-burn landing (use the lunar lander)."""
    L = LaunchConfig(body="Moon", lat_deg=0.0, lon_deg=0.0, start_mode="hover", orbit_altitude_m=alt_m, target_body="Moon")
    return L, [Phase("Powered descent", "powered_landing", 1.0, until={})]


def earth_mars_window(dep_start_day=0.0, span_days=800.0):
    """Finds the cheapest Earth->Mars Lambert transfer in the search window and starts the rocket on the departure leg."""
    from .bodies import SolarSystem; from . import transfer
    sys_ = SolarSystem(); pc = transfer.porkchop(sys_, "Earth", "Mars", dep_start_day, span_days, 120, 350, 30, 30); b = pc["best"]
    L, t = transfer.to_launch_config(sys_, "Earth", "Mars", b["dep_day"], b["tof_days"]); return L, [Phase("Coast to Mars (no mid-course correction)", "coast", 0.0, until={})]


PRESET_ROCKETS = {"Moon powered descent (lunar lander)": "Lunar lander (Moon only)"}

PRESETS = {"Earth launch to LEO": earth_leo, "LEO -> Sun dive (heliocentric retrograde burn)": leo_to_sun_dive,
           "LEO -> Mars transfer burn (illustrative)": leo_to_mars_transfer,
           "Moon powered descent (lunar lander)": moon_descent, "Earth -> Mars Lambert transfer (best window)": earth_mars_window}
