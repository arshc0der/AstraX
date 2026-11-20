# Developer guide

## Set up
```bash
python -m venv venv && venv\Scripts\activate
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v        # ~2 minutes, no GUI needed
python tools/gen_docs.py                       # regenerate generated docs
```

## Conventions
SI units internally. Docstrings on public functions (they feed API_REFERENCE). New physics gets a test against an analytic or reference value. Keep Qt out of `astrax/`.

## Recipes
### Add a celestial body
Append a `Body(...)` in `astrax/bodies.py::REFERENCE_BODIES` (GM, radius, rotation, tilt, elements, optional `Atmosphere`, `source`). Moons need `parent="Earth"` (handled for Earth–Moon in `SolarSystem.initial_state`; other parents need the same treatment). Add a test of `surface_gravity`/period.

### Add a guidance mode
1. In `Simulation._guidance` add `elif m == "my_mode": ...; return direction, throttle`.
2. Add the name to `MODES` in `ui/mission_panel.py` and to the table in `tools/gen_docs.py` (flight-plan modes).
3. Test it: build a `Phase("x", "my_mode", ...)`, step the simulation, assert behaviour.

### Add a flight-plan end condition
Extend `Simulation._phase_done` with a new `until` key; document it in `gen_docs.py`.

### Add a failure mode
In `Simulation._loads_and_failures` compute the load, add it to `self.peak`, a warning line, and an `elif` in the failure chain (`why = "..."`). Add a design limit to `structure.Limits` if user-tunable and expose it in the designer. Test with a design that trips it.

### Add an emergency/fault
Add a key to `self.faults` (reset in `reset()`), handle it in `emergency()`, apply it in `step()`/`_stage_flow()`, and a button in `ui/emergency_panel.py` that sends `worker.command("emergency", name, value)`.

### Add a telemetry variable
Add it to `Simulation.telemetry()`, then to `recorder.NUMERIC` and `UNITS`, then to `ui/telemetry.py::VARS` (label, divisor, unit).

### Add a UI panel
Create a widget in `ui/`, never call physics from the GUI thread (use `FuncWorker` or `worker.command`), add it as a tab in `MainWindow.rtabs` wrapped by `self._scroll(...)`.

### Add an example rocket / challenge
`astrax/rocket_library.py::LIBRARY` (factory returning `Rocket`) and `astrax/challenges.py::CHALLENGES` (function returning `ChallengeResult`).

## Gotchas learned the hard way
- Qt methods named `update`, `move`, `result`, `close`... must not be overridden by your own methods.
- pyqtgraph `GLGridItem`: call `setSpacing` **before** `setSize` (otherwise it builds hundreds of millions of lines).
- Never read arrays being appended by another thread: use `Recorder.arrays(...)` (locked, consistent length).
- `QAction(None, text, parent)` is invalid in PyQt6: use the two-argument form without an icon.
- Auto time-step must use **air-relative** speed for drag relaxation.

## Testing the UI without a display
The engine is fully tested. For the GUI, import `ui.*` against stub Qt classes to catch NameErrors/attribute errors (see the approach in the project history); real Qt behaviour must still be checked by running `python main.py`.

## Packaging
```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name AstraX --icon assets/logo.ico --add-data "assets;assets" --collect-all pyqtgraph main.py
```
(Linux/macOS: use `:` instead of `;` in `--add-data`.)
