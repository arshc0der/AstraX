"""User flight-computer scripts (Python). Preserves the original AstraX `mission_loop()` API.

SECURITY NOTE: scripts run in-process with a restricted builtins set. This reduces accidents but is NOT a
security sandbox - only run scripts you trust.
"""
import math, traceback

SAFE_BUILTINS = {n: __builtins__[n] if isinstance(__builtins__, dict) else getattr(__builtins__, n)
                 for n in ("abs", "min", "max", "round", "range", "len", "float", "int", "bool", "sum", "enumerate", "zip", "print", "pow", "divmod", "sorted", "any", "all", "str", "list", "dict", "tuple")}


class MissionRuntime:
    def __init__(self, sim, logger):
        self.sim, self.log = sim, logger
        self.context = {}; self.is_active = False; self.state = [1.0, 90.0, 90.0]     # throttle, pitch, heading

    def compile_script(self, text):
        sim, st, log = self.sim, self.state, self.log

        class RocketAPI:
            def set_thrust(s, v): st[0] = max(0.0, min(1.0, float(v))); sim.script_ctrl = tuple(st)
            def set_pitch(s, deg): st[1] = float(deg); sim.script_ctrl = tuple(st)      # 90 = vertical, 0 = horizontal
            def set_heading(s, deg): st[2] = float(deg); sim.script_ctrl = tuple(st)    # 90 = east
            def get_altitude(s): return sim.telemetry()["altitude_m"] / 1000.0           # km
            def get_velocity(s): return sim.telemetry()["speed_mps"]                      # m/s
            def get_surface_velocity(s): return sim.telemetry()["surface_speed_mps"]
            def get_fuel(s): return sim.telemetry()["propellant_kg"]
            def get_apoapsis(s): return sim.telemetry()["apoapsis_alt_m"] / 1000.0
            def get_periapsis(s): return sim.telemetry()["periapsis_alt_m"] / 1000.0
            def stage(s): sim.separate_next()
            def log(s, msg): log(f"USER: {msg}")

        self.context = {"__builtins__": SAFE_BUILTINS, "rocket": RocketAPI(), "math": math, "print": lambda *a: log("PRINT: " + " ".join(map(str, a)))}
        try:
            exec(text, self.context)
            if "mission_loop" not in self.context: raise ValueError("Script must define 'def mission_loop():'")
            self.is_active = True; sim.script_ctrl = tuple(st); return True
        except Exception as e:
            self.log(f"SCRIPT ERROR: {e}"); traceback.print_exc(); return False

    def disable(self): self.is_active = False; self.sim.script_ctrl = None

    def execute_step(self):
        if self.is_active:
            try: self.context["mission_loop"]()
            except Exception as e: self.log(f"RUNTIME ERROR: {e}"); self.disable()
