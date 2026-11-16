# AstraX user guide

## Workspaces
* **Simulation** - 3D viewport. Toolbar: Run/Pause (Space), Step (N), Stop, Reset (R), Stage (S), speed (0.1x ... 1000x or Custom), integrator, timestep mode, camera mode, Top/Side/Front/Iso, Reset cam, Focus (F), Record, Snapshot.
* **Rocket designer** - add/remove/reorder stages and strap-on boosters; edit dimensions, masses, engines (count, placement, thrust, Isp, nozzle), fins, legs, nose shape, Cd. The 3D model and the **ESTIMATES** table update live. "Use this rocket in simulation" restarts the simulation with it.
  * **Make your own 3D rocket:** build it from parts (any number of stages/boosters), or import your own `.obj` mesh (display only), or export the generated rocket to `.obj` for Blender.
* **Learn** - equations with live numbers for your rocket and planets.
* **Right dock** - *Mission control* (launch body, destination, site, azimuth, parking orbit, flight-plan table, Python flight computer) and *Planet inspector* (edit mass, radius, rotation, tilt, orbital elements; every body has *Reset to default*; edited bodies are flagged).
* **Bottom dock** - *Telemetry & timeline* (live readouts, 4 selectable graphs with units, compare saved runs, trajectory plots, **travel analysis** toward the Sun / any destination) and *Event log*.

## Typical flows
1. **Launch to orbit:** Mission control -> preset "Earth launch to LEO" -> Run.
2. **Fly toward the Sun or a planet:** preset "LEO -> Sun dive" (retrograde burn relative to Sun) or "LEO -> Mars transfer burn", open *Telemetry -> Trajectory & travel analysis* to see distance vs time, closest approach and ETA.
3. **Compare designs:** Run, press *Keep this run for comparison*, change the rocket, run again, tick both runs in *Graphs*.

## Logs, recording, export
* Run logs: `logs/astrax_<timestamp>.log` (Tools -> Open logs folder); events are also in the Event log dock.
* Recording: toolbar **Record** (start/stop) -> GIF (Pillow) or MP4 (needs `ffmpeg`); **Snapshot** saves PNG.
* Data: CSV (with units in headers), JSON sessions (save/load/compare), Markdown mission report (+ PNG graphs if matplotlib is installed), scenarios, rocket designs, planet configs (all readable JSON).

## Numerical accuracy
Playback speed is separate from timestep. If the CPU cannot keep up, AstraX runs *slower than requested* (status bar shows requested vs achieved acceleration) rather than coarsening the physics. Choose *fixed* dt to get explicit stability warnings, or *auto* to size dt from orbit/atmosphere resolution.
