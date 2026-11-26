# Adding or changing physics

## Checklist
1. **Define the model** - equations, inputs/outputs with SI units, assumptions, validity range.
2. **Find a reference** - textbook example, analytic solution, published dataset (with epoch/units).
3. **Implement in `astrax/`** - pure functions where possible; wire into `Simulation` only if needed.
4. **Test** - at least one test comparing to the reference with a stated tolerance; plus an integration test if it affects flights.
5. **Document** - add a row to the tables in `docs/PHYSICS.md` (model, code location, validation) and list limitations.
6. **Regenerate docs** - `python tools/gen_docs.py`.
7. **UI** - expose parameters in the right panel with tooltips/units; add manual test cases in `tools/gen_test_cases.py`.
8. **Changelog** and PR template boxes.

## Worked example: a new guidance mode
```python
# astrax/simulation.py  (inside Simulation._guidance)
elif m == "hold_apoapsis":
    ...                      # compute direction and throttle from state
    return direction, throttle
```
Then:
- add `"hold_apoapsis"` to `MODES` in `ui/mission_panel.py` and to the modes list in `tools/gen_docs.py`;
- test: build `Phase("x", "hold_apoapsis", ...)`, step, assert the behaviour (e.g. apoapsis stays within 1 km);
- document in `docs/USER_GUIDE.md` §5.2.

## Worked example: a new load/failure
See `Simulation._loads_and_failures`: compute the load, store in `self.loads`/`self.peak`, add the limit to `structure.Limits` (with default), add an `elif` to the failure chain, expose the limit in the designer, add a gauge, test a design that trips it.

## Numerical guidance
- Prefer RK4/DOPRI5 for forced dynamics, Verlet for pure gravity. Keep step control in `auto_dt()`.
- Compare against energy/angular-momentum conservation when possible.
- Mass flow is constant over a step, so mass is integrated exactly; keep that property.
- Guidance and throttle are zero-order-hold per step: do not assume continuous control.

## Scientific data
Record source, epoch, units and uncertainty next to the data (see `astrax/bodies.py`). Never modify reference data in place - edits live in the working copy with a reset path.

## Validation hygiene
Report the achieved agreement honestly (e.g. "within 1 % in the Allen–Eggers limit"). State when a test uses idealised conditions (flat, gravity-free).
