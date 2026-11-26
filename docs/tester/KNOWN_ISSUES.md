# Known issues and limitations (4.0.0)

Not bugs to re-report - but feedback on their impact is welcome.

## Model limitations (by design; see [PHYSICS](../PHYSICS.md))
- Planet positions use mean Keplerian elements (arc-minute errors), not a perturbed ephemeris.
- Simplified aerodynamics (generic transonic Cd curve, no wind, no flow separation) and a yield-stress structural check (no buckling/fatigue/flutter/slosh).
- No rotational (attitude) dynamics: the vehicle points where guidance commands.
- Capsule re-entry heating is not coupled to the live simulation (use the Re-entry calculator).
- Mars transfer flown without mid-course correction misses the planet by ~2 million km.
- Phobos/Deimos, planet textures and rendezvous guidance are not implemented yet (roadmap).

## Platform notes
- **GUI testing coverage:** the engine is heavily automated; real-window behaviour is verified manually.
- macOS: OpenGL is deprecated; blank 3D view on some releases → try `--cpu` and report.
- Windows file dialogs follow the OS theme (cannot be themed).
- Native themed title bar only on Windows 10 (1809+) and 11.
- Software OpenGL (VMs, remote desktop) is slow.
- PyQt6 is GPL/commercial: binary redistribution considerations in [THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md).

## Behaviour notes
- The survival test uses one generic ascent profile; a failure may reflect that profile rather than the design (the report says so).
- Maximum-payload search is a bisection on a non-monotonic function: treat as an estimate.
- Graph redraws happen about once per second while running (by design, for performance).

Report anything else with the *Bug report* form.
