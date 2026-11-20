"""Educational / research mode: equations, units and LIVE numbers computed from the current rocket and bodies."""
import math
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QTextBrowser, QLabel
from astrax.constants import G, G0
from astrax.orbital import hohmann

TOPICS = ["Gravity", "Orbital mechanics", "Rocket equation & staging", "Thrust-to-weight ratio", "Delta-v budget", "Orbital transfers (Hohmann)", "Atmospheric drag", "Aerodynamics: Mach, lift and heating", "Structural loads & failure modes", "Changing an orbit"]


class EducationPanel(QWidget):
    def __init__(self, get_rocket, get_system):
        super().__init__(); self.get_rocket, self.get_system = get_rocket, get_system
        v = QVBoxLayout(self); self.combo = QComboBox(); self.combo.addItems(TOPICS); self.combo.currentIndexChanged.connect(self.refresh); v.addWidget(self.combo)
        self.view = QTextBrowser(); v.addWidget(self.view)
        v.addWidget(QLabel("Simplified models are labelled. Change masses/rocket properties and revisit this page to watch the numbers change.", objectName="muted")); self.refresh()

    def refresh(self, *_):
        r, s = self.get_rocket(), self.get_system(); e = r.estimates(); earth = s.get("Earth"); t = TOPICS[self.combo.currentIndex()]; H = f"<h3>{t}</h3>"
        if t == "Gravity":
            H += (f"<p><b>Universal gravitation:</b> F = G m<sub>1</sub> m<sub>2</sub> / r<sup>2</sup>, with G = {G:.5e} m<sup>3</sup> kg<sup>-1</sup> s<sup>-2</sup>.</p>"
                  f"<p>Surface gravity g = GM/R<sup>2</sup>. Earth (current settings): GM = {earth.gm:.6e} m<sup>3</sup>/s<sup>2</sup>, R = {earth.radius_m / 1e3:.1f} km &rArr; <b>g = {earth.surface_gravity:.3f} m/s<sup>2</sup></b>.</p>"
                  f"<p>Weight of the loaded rocket at sea level: {e['launch_mass_kg'] * earth.surface_gravity / 1e6:.2f} MN. <i>Try:</i> double Earth's mass in the Planet Inspector and watch orbital speeds rise by &radic;2.</p>"
                  "<p><i>Model:</i> point masses, full N-body summation; no J2 oblateness.</p>")
        elif t == "Orbital mechanics":
            r0 = earth.radius_m + 400e3; v = math.sqrt(earth.gm / r0); T = 2 * math.pi * math.sqrt(r0 ** 3 / earth.gm)
            H += (f"<p>Circular orbit: v = &radic;(&mu;/r), period T = 2&pi;&radic;(r<sup>3</sup>/&mu;). Vis-viva: v<sup>2</sup> = &mu;(2/r - 1/a). Specific energy &epsilon; = v<sup>2</sup>/2 - &mu;/r = -&mu;/2a.</p>"
                  f"<p>At 400 km altitude: <b>v = {v:,.0f} m/s</b>, <b>T = {T / 60:.1f} min</b>. Escape speed there: {math.sqrt(2) * v:,.0f} m/s.</p>"
                  "<p>Orbit elements shown in Telemetry (a, e, i, apoapsis, periapsis) are two-body elements about the currently dominant body.</p>")
        elif t == "Rocket equation & staging":
            H += (f"<p><b>Tsiolkovsky:</b> &Delta;v = I<sub>sp</sub> g<sub>0</sub> ln(m<sub>0</sub>/m<sub>f</sub>), g<sub>0</sub> = {G0}.</p><p>Your vehicle: mass ratio {e['mass_ratio']:.2f}, <b>&Delta;v = {e['delta_v_mps']:,.0f} m/s</b> (ESTIMATE).</p><ul>")
            for st in e["stages"]: H += f"<li>{st['stage']}: &Delta;v {st['dv']:,.0f} m/s, m<sub>0</sub> {st['m0']:,.0f} kg &rarr; m<sub>f</sub> {st['m1']:,.0f} kg</li>"
            single = r.stages[0].engine.isp_vac_s * G0 * math.log(e["launch_mass_kg"] / (e["launch_mass_kg"] - e["propellant_kg"]))
            H += f"</ul><p><b>Why stage?</b> Dropping empty tanks removes dead mass. Same propellant burned in ONE stage (no jettison) would give only &Delta;v = {single:,.0f} m/s.</p>"
        elif t == "Thrust-to-weight ratio":
            H += f"<p>T/W = F / (m g). Lift-off needs T/W &gt; 1; ascent gravity loss grows as T/W &rarr; 1.</p><p>Your vehicle: <b>{e['twr_sl']:.2f}</b> at sea level on Earth (thrust {e['thrust_sl_n'] / 1e6:.2f} MN).</p><p>Same rocket on the Moon (g = {s.get('Moon').surface_gravity:.2f} m/s<sup>2</sup>) would be T/W = {e['thrust_sl_n'] / (e['launch_mass_kg'] * s.get('Moon').surface_gravity):.1f}.</p>"
        elif t == "Delta-v budget":
            g = earth.gm; r = earth.radius_m + 200e3
            H += (f"<p>Typical budget to 200 km LEO: orbital speed {math.sqrt(g / r):,.0f} m/s + gravity loss (~1,000-1,500 m/s) + drag loss (~100-300 m/s) - Earth-rotation help (up to ~{2 * math.pi * earth.radius_m / earth.rotation_period_s:,.0f} m/s at the equator).</p>"
                  f"<p>Your rocket's ideal &Delta;v is {e['delta_v_mps']:,.0f} m/s. Compare with the simulated &Delta;v spent in Telemetry: the difference shows real losses.</p>")
        elif t == "Orbital transfers (Hohmann)":
            sun = s.bodies[0]; h = hohmann(sun.gm, s.get("Earth").a, s.get("Mars").a)
            H += (f"<p>Two-impulse transfer: &Delta;v<sub>1</sub> = &radic;(&mu;/r<sub>1</sub>)(&radic;(2r<sub>2</sub>/(r<sub>1</sub>+r<sub>2</sub>)) - 1), time of flight = &pi;&radic;(a<sub>t</sub><sup>3</sup>/&mu;).</p>"
                  f"<p>Earth &rarr; Mars heliocentric (circular, coplanar approx.): &Delta;v<sub>1</sub> = {h['dv1']:,.0f} m/s, &Delta;v<sub>2</sub> = {h['dv2']:,.0f} m/s, <b>TOF = {h['tof'] / 86400:.0f} days</b>. The planet's phase angle (launch window) matters and is not included here.</p>")
        elif t == "Atmospheric drag":
            from astrax.atmosphere import density
            q = 0.5 * density(earth, 11000) * 400 ** 2
            H += (f"<p>F<sub>d</sub> = &frac12; &rho; C<sub>d</sub> A v<sup>2</sup>; dynamic pressure q = &frac12; &rho; v<sup>2</sup>.</p><p>Your Cd = {r.cd}, A = {r.reference_area_m2:.2f} m<sup>2</sup>. At 11 km, 400 m/s: &rho; = {density(earth, 11000):.3f} kg/m<sup>3</sup>, q = {q / 1e3:.1f} kPa, drag = {q * r.cd * r.reference_area_m2 / 1e3:.0f} kN.</p>"
                  "<p><i>Model:</i> constant Cd; no Mach/angle-of-attack dependence, no lift. Earth uses US Standard Atmosphere 1976 densities.</p>")
        elif t.startswith("Aerodynamics"):
            from astrax import aero
            a0 = aero.speed_of_sound(earth, 0); a11 = aero.speed_of_sound(earth, 11000)
            H += (f"<p><b>Mach number</b> M = v / a, with speed of sound a = &radic;(&gamma; R T): {a0:.0f} m/s at sea level, {a11:.0f} m/s at 11 km (T = 216.65 K).</p>"
                  f"<p><b>Drag</b> F<sub>d</sub> = &frac12; &rho; v<sup>2</sup> C<sub>d</sub>(M) A. C<sub>d</sub> is not constant: factor vs your base C<sub>d</sub> = {r.cd}: "
                  f"M 0.3 &rarr; {aero.cd_factor(0.3):.2f}, M 0.9 &rarr; {aero.cd_factor(0.9):.2f}, <b>M 1.05 &rarr; {aero.cd_factor(1.05):.2f}</b> (transonic peak), M 3 &rarr; {aero.cd_factor(3):.2f}.</p>"
                  f"<p><b>Lift / normal force</b> N = q A C<sub>N&alpha;</sub> sin&alpha; cos&alpha;. Your C<sub>N&alpha;</sub> (Barrowman est.) = {r.cn_alpha():.2f} per rad; centre of pressure {e['cop_m']:.1f} m vs centre of mass {e['com_m']:.1f} m &rArr; static margin {e['static_margin_cal']:.2f} calibres "
                  f"({'stable' if e['static_margin_cal'] > 0 else 'UNSTABLE - needs active control'}).</p>"
                  f"<p><b>Heating</b> (Sutton-Graves): q&#775; = k &radic;(&rho;/R<sub>n</sub>) v<sup>3</sup>. At 2 km/s and &rho; = 1 g/m<sup>3</sup> with R<sub>n</sub> = {r.nose_radius_m} m: {aero.stagnation_heat_flux(earth, 1e-3, 2000, r.nose_radius_m) / 1e3:.0f} kW/m<sup>2</sup>.</p>"
                  "<p><i>Model:</i> generic transonic curve, no wind-tunnel data, no flow separation, no shock interaction, no real-gas effects.</p>")
        elif t.startswith("Structural"):
            from astrax import structure
            st = r.stages[0]; H += (f"<p>Each tank section is checked as a thin-walled tube: &sigma; = N/(2&pi;R t) + M/(&pi;R<sup>2</sup> t), N = axial load from the mass above times the acceleration, M = aerodynamic bending moment from the normal force.</p>"
                  f"<p>{st.name}: {st.material}, wall {st.wall_thickness_mm} mm, shell mass {structure.shell_mass(st):,.0f} kg. Design limits: max-Q {r.limits.max_q_pa / 1e3:.0f} kPa, {r.limits.max_axial_g:.1f} g, nose heating {r.limits.max_heat_flux_w_m2 / 1e3:.0f} kW/m<sup>2</sup>, factor of safety {r.limits.factor_of_safety}.</p>"
                  "<p><b>Failure modes simulated:</b> aerodynamic overload, axial overload, nose overheating, skin stress reaching yield, and loss of control (unstable vehicle without active control). <b>Not simulated:</b> buckling, fatigue, flutter, slosh, engine failure explosions.</p>"
                  "<p>Use <i>Rocket designer &rarr; Run survival test</i> to check a design, then <i>Watch in 3D</i> to see it.</p>")
        elif t == "Changing an orbit":
            H += ("<p>A burn changes velocity at one point; the orbit then passes through that point again. <b>Prograde</b> burn raises the opposite side of the orbit (apogee), <b>retrograde</b> lowers it; <b>normal</b> burns rotate the orbital plane (inclination); <b>radial</b> burns rotate the line of apsides.</p>"
                  "<p>Plane change by angle &Delta;i at speed v: &Delta;v = 2 v sin(&Delta;i/2) (pure rotation) - expensive, so do it where v is small. Hohmann: two prograde burns.</p>"
                  "<p>Open <i>Orbit analysis</i> in the right panel: see how every stage burn changed the orbit, preview a manoeuvre, draw the predicted path in 3D, or apply an ideal impulse.</p>")
        self.view.setHtml(H)
