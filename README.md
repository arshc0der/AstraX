# 🚀 AstraX — Pro Solar System Architect

> An enterprise-grade **solar system simulator & mission design lab** with real physics, real code, and real space missions.

<p align="left">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" />
  <img src="https://img.shields.io/badge/status-Stable-brightgreen.svg" />
  <img src="https://img.shields.io/badge/license-MIT-green.svg" />
  <img src="https://img.shields.io/badge/python-3.10%2B-yellow.svg" />
  <img src="https://img.shields.io/badge/physics-N--Body-orange.svg" />
  <img src="https://img.shields.io/badge/rendering-OpenGL-success.svg" />
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg" />
  <img src="https://img.shields.io/badge/simulation-Real%20Orbital%20Mechanics-red.svg" />
  <img src="https://img.shields.io/badge/contributions-welcome-yellow.svg" />
  <img src="https://img.shields.io/github/stars/arshc0der/AstraX?style=social" />
  <img src="https://img.shields.io/github/forks/arshc0der/AstraX?style=social" />
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/arshc0der/ASTRA-X-UNIVERSE-SIMULATOR/refs/heads/main/Testing/preview/logo.jpg" width="75%" />
</p>

---

## 🌌 Overview

**AstraX** is an open-source spaceflight simulation laboratory: design rockets (stages, boosters, engines, fins, legs or your own OBJ model), edit planets, fly missions with real N-body gravity, and analyse telemetry.

> ⚠️ Results are **not validated mission predictions**. See [`docs/PHYSICS.md`](docs/PHYSICS.md) for assumptions, tests and limitations.

### Features
- **Physics (headless, tested):** N-body gravity, Keplerian elements, RK4 / adaptive Dormand-Prince / velocity Verlet, variable-mass rocket equation, pressure-dependent thrust, atmospheric drag, multi-stage + strap-on boosters, surface contact, flight-plan guidance (gravity turn, closed-loop insertion, prograde/retrograde burns).
- **Rocket designer:** live procedural 3D rocket, custom stage stacks, OBJ import/export, estimated delta-v / T/W / CoM / CoP / inertia (clearly labelled *estimates*).
- **Planet inspector:** editable mass, radius, rotation, tilt, orbital elements; per-body reset; sources and limitations shown.
- **Time controls:** 0.1x - 1000x + custom; separate timestep; stability warnings; honest "achieved vs requested" speed.
- **Telemetry & analysis:** selectable graphs with units, run comparison, trajectory and travel-to-Sun/planet analysis, CSV / JSON session / Markdown report export.
- **Logs & recording:** rotating run logs, event log, GIF/MP4 viewport recording, PNG snapshots.
- **Survival & safety:** Mach-dependent aerodynamics, structural/thermal/control failure model, one-click **design survival test** with 3D replay, abort with parachute capsule, failure injection.
- **Orbit analysis:** orbit change per event, maneuver planner, predicted path overlay.
- **Customisation:** extra 3D/graph windows, themes, font size.
- **Flight computer:** original Python `mission_loop()` API preserved.

**Start with the [User Guide](docs/USER_GUIDE.md).** Example output: [`docs/examples/`](docs/examples/).

---

## 🛠 Installation

### 🔹 Clone Repository

```bash
git clone https://github.com/arshc0der/AstraX.git
cd AstraX
```

### 🔹 (Optional) Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 🔹 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Launch Simulator

```bash
python main.py
```

✔ Automatic **High-DPI / 4K scaling support**

---

## 🎮 Mission Workflow

### Phase 1 — Rocket Design

1. Configure **Dry Mass**
2. Set **Fuel Capacity**
3. Tune **Engine Thrust**
4. Click **INITIALIZE FLIGHT SYSTEMS**

### Phase 2 — Mission Control

1. Write your `mission_loop()`
2. Press **LAUNCH MISSION**
3. Observe real-time 3D trajectory

---

## 📝 Example Flight Program

```python
def mission_loop():
    alt_km = rocket.get_altitude()
    vel = rocket.get_velocity()

    if alt_km < 50:
        rocket.set_pitch(90)
        rocket.set_thrust(1.0)
    elif alt_km < 150:
        rocket.set_pitch(60)
        rocket.set_thrust(1.0)
    elif vel < 7500:
        rocket.set_pitch(0)
        rocket.set_thrust(1.0)
    else:
        rocket.set_thrust(0.0)
```

---

## 🧪 Tests

```bash
python -m unittest discover -s tests -v
```

## 📂 Project Structure

```text
AstraX/
├── main.py                 # PyQt6 entry point
├── astrax/                 # headless engine - no Qt/OpenGL imports
│   ├── simulation.py  bodies.py  orbital.py  integrators.py  atmosphere.py
│   ├── rocket.py  rocket_mesh.py  missions.py  runtime.py  recorder.py  project.py
├── ui/                     # PyQt6 interface
├── tests/                  # unit + integration tests
├── docs/                   # PHYSICS.md, USER_GUIDE.md, examples/
└── legacy/core/            # original engine, kept for reference
```

---

## 🤝 Contributing

Contributions are welcome 🚀

1. 🍴 Fork the repository
2. 🌱 Create a feature branch
3. 🛠 Commit your changes
4. 🔁 Open a Pull Request

If you like Astra-X, please ⭐ **star the repo** — it helps a lot!

---

## 📦 Deployment (Standalone EXE)

```bash
python -m PyInstaller --noconsole --onefile \
--name="AstraX" \
--icon="assets/logo.png" \
--add-data "assets;assets" --collect-all pyqtgraph \
--version-file="version_info.txt" \
main.py
```

---

## 📢 Stay Connected

| Platform | Link                                                                                     |
| -------- | ---------------------------------------------------------------------------------------- |
| GitHub   | [https://github.com/arshc0der](https://github.com/arshc0der)                             |
| Issues   | [https://github.com/arshc0der/AstraX/issues](https://github.com/arshc0der/AstraX/issues) |

---

## 📜 License

Distributed under the **MIT License**.
© 2026 **Arsh**

---

### ❤️ Built for engineers, students, researchers & space dreamers.

> **Astra-X — Not a game. A real mission simulator.**

---
