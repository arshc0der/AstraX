"""Rocket design model: stages, engines, fins, legs, boosters + derived estimates.

All values SI. Stage 0 launches first (bottom of the stack). Boosters (kind="booster") are strapped on
beside the first core stage, fire in parallel with it, and are discarded when empty.

ESTIMATES vs SIMULATION: everything in `Rocket.estimates()` is an analytic estimate (Tsiolkovsky,
vacuum Isp, no gravity/drag losses). Simulated values come from `Simulation` telemetry.
"""
from __future__ import annotations
import copy, json, math
from dataclasses import dataclass, field, asdict
from .constants import G0
from .structure import Limits, MATERIALS, shell_mass


@dataclass
class Engine:
    count: int = 1
    thrust_vac_n: float = 100e3        # per engine
    isp_vac_s: float = 300.0
    isp_sl_s: float = 270.0
    nozzle_diameter_m: float = 0.8
    nozzle_length_m: float = 1.2
    placement: str = "single"           # single | ring | octaweb | cluster
    gimbal_deg: float = 5.0

    @property
    def total_thrust_vac(self): return self.count * self.thrust_vac_n
    @property
    def mdot(self): return self.total_thrust_vac / (self.isp_vac_s * G0)
    @property
    def thrust_sl(self): return self.total_thrust_vac * self.isp_sl_s / self.isp_vac_s


@dataclass
class Stage:
    name: str = "Stage"
    kind: str = "core"                  # core | booster
    diameter_m: float = 3.0
    length_m: float = 20.0
    dry_mass_kg: float = 5000.0
    propellant_kg: float = 50000.0
    propellant_capacity_kg: float = 0.0  # 0 -> same as propellant_kg
    engine: Engine = field(default_factory=Engine)
    interstage_length_m: float = 0.8
    fin_count: int = 0
    fin_span_m: float = 1.5
    fin_root_chord_m: float = 2.5
    fin_tip_chord_m: float = 1.0
    leg_count: int = 0
    leg_length_m: float = 6.0
    separation: str = "burnout"         # burnout | time | manual
    separation_time_s: float = 0.0
    tank_split: bool = True             # draw separate fuel/oxidiser tank sections
    color: tuple = (0.92, 0.92, 0.95, 1.0)
    booster_count: int = 1              # only for kind == booster (identical strap-ons)
    cd: float = 0.0                     # 0 -> use rocket-level Cd
    material: str = "Al-Li 2195"         # structural material (see structure.MATERIALS)
    wall_thickness_mm: float = 4.0       # tank/skin wall thickness used by the stress check

    @property
    def capacity(self): return self.propellant_capacity_kg or self.propellant_kg
    @property
    def wet_mass(self): return self.dry_mass_kg + self.propellant_kg


@dataclass
class Nose:
    shape: str = "ogive"                # ogive | conic | parabolic | elliptical | von_karman
    length_m: float = 6.0
    base_diameter_m: float = 3.0
    mass_kg: float = 0.0                # fairing mass (part of payload mass if 0)
    color: tuple = (0.95, 0.95, 0.98, 1.0)


@dataclass
class Rocket:
    name: str = "Custom Rocket"
    stages: list = field(default_factory=lambda: [Stage()])
    payload_mass_kg: float = 1000.0
    nose: Nose = field(default_factory=Nose)
    cd: float = 0.35                    # reference drag coefficient (user editable)
    custom_mesh_path: str = ""          # optional OBJ model used for display only
    nose_radius_m: float = 0.3          # nose-tip radius of curvature for stagnation heating
    intended_body: str = "Earth"        # body this vehicle launches from (used for thrust-to-weight checks)
    active_control: bool = True         # TVC/fins keep attitude; if False an unstable vehicle tumbles
    limits: Limits = field(default_factory=Limits)
    notes: str = ""

    # ---------- structure helpers ----------
    @property
    def cores(self): return [s for s in self.stages if s.kind == "core"]
    @property
    def boosters(self): return [s for s in self.stages if s.kind == "booster"]
    @property
    def diameter_m(self): return max([s.diameter_m for s in self.cores] or [1.0])
    @property
    def reference_area_m2(self): return math.pi * (self.diameter_m / 2) ** 2

    def stack_layout(self):
        """Return list of (stage, z_base, z_top) for core stages (z=0 at base of first core)."""
        z, out = 0.0, []
        for s in self.cores:
            out.append((s, z, z + s.length_m))
            z += s.length_m + s.interstage_length_m
        return out

    @property
    def total_height_m(self):
        lay = self.stack_layout()
        top = lay[-1][2] if lay else 0.0
        return top + self.nose.length_m

    def total_mass(self, include_boosters=True):
        m = self.payload_mass_kg + self.nose.mass_kg
        for s in self.stages:
            if s.kind == "booster":
                if include_boosters: m += s.wet_mass * s.booster_count
            else:
                m += s.wet_mass
        return m

    # ---------- derived estimates ----------
    def _lumps(self, fuel_fraction=None):
        """(mass, z_centre, length, radius) lumps for CoM / inertia."""
        lumps = []
        lay = {id(s): (zb, zt) for s, zb, zt in self.stack_layout()}
        first = self.cores[0] if self.cores else None
        for s in self.stages:
            if s.kind == "core":
                zb, zt = lay[id(s)]
            else:   # booster alongside first core
                zb, zt = 0.0, s.length_m
            ff = (s.propellant_kg / s.capacity) if fuel_fraction is None else fuel_fraction
            n = s.booster_count if s.kind == "booster" else 1
            r = s.diameter_m / 2
            off = (self.diameter_m / 2 + r) if s.kind == "booster" else 0.0
            lumps.append((s.dry_mass_kg * n, (zb + zt) / 2, s.length_m, r, off))
            lumps.append((s.propellant_kg * n, zb + (zt - zb) * ff / 2, max(1e-3, (zt - zb) * ff), r, off))
        top = lay[id(self.cores[-1])][1] if self.cores else 0
        ztop = (self.stack_layout()[-1][2] if self.cores else 0)
        lumps.append((self.payload_mass_kg + self.nose.mass_kg, ztop + self.nose.length_m * 0.4,
                      self.nose.length_m, self.nose.base_diameter_m / 2, 0.0))
        return lumps

    def center_of_mass(self):
        l = self._lumps(); M = sum(x[0] for x in l)
        return sum(x[0] * x[1] for x in l) / M if M else 0.0

    def moments_of_inertia(self):
        """(Ixx=Iyy transverse, Izz axial) kg m^2 about the CoM; uniform-cylinder lumps (estimate)."""
        l = self._lumps(); zc = self.center_of_mass()
        Ixx = Izz = 0.0
        for m, z, L, r, off in l:
            Izz += 0.5 * m * r * r + m * off * off
            Ixx += m * (3 * r * r + L * L) / 12 + m * (z - zc) ** 2 + m * off * off / 2
        return Ixx, Izz

    def cn_alpha(self):
        """Normal-force slope CN_alpha (per radian) from the simplified Barrowman sum."""
        return self._barrowman()[0]

    def center_of_pressure(self):
        return self._barrowman()[1]

    def _barrowman(self):
        """Simplified Barrowman estimate (nose + body + first-stage fins), m from base."""
        D = self.diameter_m; Ln = self.nose.length_m
        z_nose_base = self.total_height_m - Ln
        cn_n, x_n = 2.0, {"conic": 2 / 3, "ogive": 0.466, "parabolic": 0.5, "elliptical": 0.333,
                          "von_karman": 0.437}.get(self.nose.shape, 0.466) * Ln
        xcp_nose = self.total_height_m - Ln + (Ln - x_n)   # measured from base
        num, den = cn_n * xcp_nose, cn_n
        for s, zb, zt in self.stack_layout():
            if s.fin_count:
                Cr, Ct, span = s.fin_root_chord_m, s.fin_tip_chord_m, s.fin_span_m
                N = s.fin_count; d = s.diameter_m; sm = math.sqrt(span ** 2 + ((Cr - Ct) / 2) ** 2)
                cnf = (1 + (d / 2) / (span + d / 2)) * (4 * N * (span / d) ** 2) / (1 + math.sqrt(1 + (2 * sm / (Cr + Ct)) ** 2))
                # Barrowman: fin CP measured from fin leading edge at root chord (swept-trapezoid fin)
                xf_le = (Cr - Ct) * (Cr + 2 * Ct) / (3 * (Cr + Ct)) + (Cr + Ct - Cr * Ct / (Cr + Ct)) / 6
                xf = zb + (Cr - Cr) + xf_le   # fin root leading edge assumed at stage base
                num += cnf * xf; den += cnf
        return den, num / den

    def estimates(self):
        """Analytic ESTIMATES (not simulation results)."""
        cores = self.cores
        boost_thrust_sl = sum(b.engine.thrust_sl * b.booster_count for b in self.boosters)
        launch_mass = self.total_mass()
        first = cores[0] if cores else None
        thrust_sl = (first.engine.thrust_sl if first else 0.0) + boost_thrust_sl
        # stage-by-stage delta-v (boosters folded into first core burn, mass-flow weighted Isp)
        mass = launch_mass; dv_total = 0.0; burn_total = 0.0; rows = []
        groups = []
        if self.boosters and first:
            groups.append(("Boosters+"+first.name, self.boosters, first))
        for i, s in enumerate(cores):
            if i == 0 and self.boosters: continue
            groups.append((s.name, [], s))
        # handle boosters: burn together then drop
        mass = launch_mass
        if self.boosters and first:
            bm = sum(b.propellant_kg * b.booster_count for b in self.boosters)
            f_b = sum(b.engine.total_thrust_vac * b.booster_count for b in self.boosters)
            md_b = sum(b.engine.mdot * b.booster_count for b in self.boosters)
            t_b = bm / md_b if md_b else 0
            f_c, md_c = first.engine.total_thrust_vac, first.engine.mdot
            isp_eff = (f_b + f_c) / ((md_b + md_c) * G0)
            m1 = mass - (md_b + md_c) * t_b
            dv = isp_eff * G0 * math.log(mass / m1) if m1 > 0 else 0
            rows.append(dict(stage="Boosters", dv=dv, burn_s=t_b, m0=mass, m1=m1)); dv_total += dv; burn_total += t_b
            mass = m1 - sum(b.dry_mass_kg * b.booster_count for b in self.boosters)
            first_prop = first.propellant_kg - md_c * t_b
        else:
            first_prop = first.propellant_kg if first else 0
        for i, s in enumerate(cores):
            prop = first_prop if i == 0 else s.propellant_kg
            md = s.engine.mdot
            m0 = mass; m1 = m0 - prop
            dv = s.engine.isp_vac_s * G0 * math.log(m0 / m1) if (m1 > 0 and m0 > m1) else 0.0
            bt = prop / md if md else 0
            rows.append(dict(stage=s.name, dv=dv, burn_s=bt, m0=m0, m1=m1)); dv_total += dv; burn_total += bt
            mass = m1 - s.dry_mass_kg
        final_mass = rows[-1]["m1"] if rows else launch_mass
        # peak thrust acceleration (vacuum, no drag/gravity) = F / m at the end of each burn
        max_acc = 0.0
        for r_, s_ in zip(rows, ([None] if self.boosters else []) + cores):
            f_ = (first.engine.total_thrust_vac + boost_thrust_sl) if (s_ is None or s_ is first) and first else (s_.engine.total_thrust_vac if s_ else 0)
            if r_["m1"] > 0: max_acc = max(max_acc, f_ / r_["m1"])
        com_, cop_ = self.center_of_mass(), self.center_of_pressure()
        return dict(
            launch_mass_kg=launch_mass, dry_mass_kg=sum(s.dry_mass_kg * (s.booster_count if s.kind == "booster" else 1) for s in self.stages) + self.payload_mass_kg,
            propellant_kg=sum(s.propellant_kg * (s.booster_count if s.kind == "booster" else 1) for s in self.stages),
            mass_ratio=launch_mass / final_mass if final_mass else math.inf,
            twr_sl=thrust_sl / (launch_mass * 9.80665) if launch_mass else 0.0, thrust_sl_n=thrust_sl,
            twr_local=thrust_sl / (launch_mass * SURFACE_G.get(self.intended_body, 9.80665)) if launch_mass else 0.0,
            delta_v_mps=dv_total, burn_time_s=burn_total,
            max_accel_ms2=max_acc,
            stages=rows, height_m=self.total_height_m, diameter_m=self.diameter_m,
            com_m=com_, cop_m=cop_, static_margin_cal=(com_ - cop_) / max(self.diameter_m, 1e-9),
            inertia_transverse_kgm2=self.moments_of_inertia()[0], inertia_axial_kgm2=self.moments_of_inertia()[1],
            reference_area_m2=self.reference_area_m2, label="ESTIMATE (analytic, vacuum Isp, no losses)")

    def validate(self) -> list[str]:
        w = []
        if not self.cores: w.append("Rocket has no core stage.")
        for s in self.stages:
            if s.engine.count < 1: w.append(f"{s.name}: needs at least 1 engine.")
            if s.propellant_kg > s.capacity + 1e-6: w.append(f"{s.name}: propellant exceeds capacity.")
            if s.dry_mass_kg <= 0: w.append(f"{s.name}: dry mass must be positive.")
            if s.engine.isp_vac_s < s.engine.isp_sl_s: w.append(f"{s.name}: vacuum Isp should be >= sea-level Isp.")
        for s in self.stages:
            if shell_mass(s) > 0.8 * s.dry_mass_kg: w.append(f"{s.name}: wall thickness implies a {shell_mass(s):,.0f} kg shell, close to/above the dry mass - raise dry mass or thin the wall.")
        e = self.estimates() if self.cores else None
        if e and e["twr_local"] < 1.0: w.append(f"Launch T/W = {e['twr_local']:.2f} < 1: vehicle cannot lift off from {self.intended_body}.")
        return w

    # ---------- persistence ----------
    def to_dict(self): return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Rocket":
        d = copy.deepcopy(d)
        stages = []
        for sd in d.pop("stages", []):
            eng = Engine(**sd.pop("engine", {}))
            sd["color"] = tuple(sd.get("color", (0.92, 0.92, 0.95, 1.0)))
            stages.append(Stage(engine=eng, **sd))
        lim = Limits(**d.pop("limits", {}))
        nd = d.pop("nose", {}); nd["color"] = tuple(nd.get("color", (0.95, 0.95, 0.98, 1.0)))
        nose = Nose(**nd)
        return Rocket(stages=stages, nose=nose, limits=lim, **d)

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"astrax_format": "rocket/1", **self.to_dict()}, f, indent=2)

    @staticmethod
    def load(path) -> "Rocket":
        with open(path, encoding="utf-8") as f: d = json.load(f)
        d.pop("astrax_format", None)
        return Rocket.from_dict(d)


SURFACE_G = {"Earth": 9.80665, "Moon": 1.62, "Mars": 3.71, "Venus": 8.87, "Mercury": 3.70}   # m/s^2, NASA fact sheets


def default_rocket() -> Rocket:
    """Illustrative two-stage kerolox rocket with rough Falcon-9-class numbers (NOT an official model)."""
    s1 = Stage("Stage 1", "core", 3.7, 42.0, 25600, 395700, 0,
               Engine(9, 914e3, 311, 282, 1.0, 1.4, "octaweb", 5), 1.0, 4, 1.8, 2.8, 1.0, 4, 7.0, "burnout")
    s2 = Stage("Stage 2", "core", 3.7, 12.0, 4000, 92670, 0,
               Engine(1, 934e3, 348, 311, 2.4, 3.0, "single", 5), 0.5, 0, 0, 0, 0, 0, 0, "burnout")
    return Rocket("Falcon-class demo (illustrative)", [s1, s2], 10000.0, Nose("ogive", 6.0, 3.7, 1500.0), 0.30)
