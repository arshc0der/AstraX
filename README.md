<div align="center">

<img src="assets/banner.png" alt="AstraX - open-source spaceflight simulation laboratory" width="860">

# AstraX

**Design rockets. Fly them in 3D. Test whether they survive. Plan Mars windows. Analyse every orbit.**

*An open-source spaceflight simulation laboratory for students, educators, hobbyists and researchers.*

[![CI](https://github.com/arshc0der/AstraX/actions/workflows/ci.yml/badge.svg)](https://github.com/arshc0der/AstraX/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/arshc0der/AstraX?include_prereleases&label=release)](https://github.com/arshc0der/AstraX/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](docs/INSTALLATION.md)
[![Stars](https://img.shields.io/github/stars/arshc0der/AstraX?style=social)](https://github.com/arshc0der/AstraX/stargazers)
[![Forks](https://img.shields.io/github/forks/arshc0der/AstraX?style=social)](https://github.com/arshc0der/AstraX/network/members)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-Contributor%20Covenant-purple.svg)](CODE_OF_CONDUCT.md)
[![Docs](https://img.shields.io/badge/docs-read-informational)](docs/README.md)

[**Quick start**](#-quick-start) · [**Screenshots**](#-screenshots) · [**Features**](#-features) · [**Documentation**](#-documentation) · [**Contributing**](#-contributing) · [**FAQ**](#-faq)

</div>

> [!IMPORTANT]
> **Scientific honesty.** AstraX uses simplified, documented models. Results are for learning, design exploration and research prototyping - **not validated mission predictions**. Every model's assumptions, limits and validation status are listed in [docs/PHYSICS.md](docs/PHYSICS.md).

---

## 🚀 What is AstraX?

AstraX is a **desktop application** (Python, PyQt6, OpenGL, NumPy) that behaves like a small aerospace laboratory:

- 🛠️ **Build** a rocket from stages, boosters, engines, fins and legs - or import your own 3D model.
- 🔥 **Launch** it in a real-time 3D scene with N-body gravity, atmosphere, drag, staging, plume and debris.
- 🧪 **Test** the design: one click runs a full ascent and tells you *PASS or FAIL* - with the exact reason, margins and a 3D replay of the breakup.
- 🛰️ **Study** orbits, plan burns, find Earth→Mars launch windows, land on the Moon, calculate re-entry heating.
- 📊 **Analyse** everything: live telemetry, graphs, ground track, CSV and report export, GIF/MP4 recording.

It has a **headless physics engine** (`astrax/`) with no GUI dependency, covered by **70+ automated tests**, and a **dockable mission-control interface** (`ui/`).

## 🖼️ Screenshots

<p align="center"><img src="docs/screenshots/01-main-window.png" alt="Main window" width="900"></p>

<table>
<tr>
<td width="50%"><img src="docs/screenshots/02-launch-liftoff.png" alt="Liftoff with launch camera"><br><sub><b>Launch camera</b> - plume, pad, banners</sub></td>
<td width="50%"><img src="docs/screenshots/04-rocket-designer.png" alt="Rocket designer"><br><sub><b>Rocket designer</b> - live 3D preview, estimates</sub></td>
</tr>
<tr>
<td><img src="docs/screenshots/05-survival-test.png" alt="Survival test"><br><sub><b>Survival test</b> - PASS/FAIL with margins</sub></td>
<td><img src="docs/screenshots/09-launch-windows.png" alt="Porkchop plot"><br><sub><b>Launch windows</b> - Lambert porkchop plot</sub></td>
</tr>
</table>

<details>
<summary><b>See all screenshots</b> (click to expand)</summary>

| | | |
|---|---|---|
| ![](docs/screenshots/03-stage-separation.png) **Stage separation** | ![](docs/screenshots/06-breakup.png) **Failure / breakup** | ![](docs/screenshots/07-flight-safety.png) **Flight safety & abort** |
| ![](docs/screenshots/08-orbit-analysis.png) **Orbit analysis** | ![](docs/screenshots/10-mars-transfer.png) **Mars transfer** | ![](docs/screenshots/11-moon-landing.png) **Powered Moon landing** |
| ![](docs/screenshots/12-telemetry-graphs.png) **Telemetry** | ![](docs/screenshots/13-ground-track.png) **Ground track** | ![](docs/screenshots/14-planet-inspector.png) **Planet inspector** |
| ![](docs/screenshots/15-studies.png) **Studies** | ![](docs/screenshots/16-settings-graphics.png) **Graphics settings** | ![](docs/screenshots/17-multi-window.png) **Multi-window** |
| ![](docs/screenshots/18-splash.png) **Animated splash** | ![](docs/screenshots/19-themes.png) **Themes** | ![](docs/screenshots/20-reentry.png) **Re-entry calculator** |

</details>

## ✨ Features

<table>
<tr><td width="50%" valign="top">

### Rockets & design
- Procedural 3D rocket: stages, strap-on boosters, engine clusters, fins, landing legs, 5 nose shapes
- Import/export **OBJ**; save/load JSON
- 6 illustrative example rockets
- Live **estimates**: Δv, T/W, mass ratio, CoM/CoP, static margin, inertia
- Materials, wall thickness, design limits

### Physics engine
- N-body gravity: Sun, 8 planets, Moon
- RK4 · adaptive Dormand-Prince · velocity Verlet
- Variable-mass rocket equation, pressure-dependent thrust
- Mach-dependent drag, angle-of-attack lift, nose heating
- Staging, surface contact, debris, abort + parachute
- Stability warnings for unsuitable timesteps

</td><td width="50%" valign="top">

### Testing designs
- **Survival test** with verdict, margins and 3D replay
- Failure model: overload, overheating, skin yield, loss of control
- Failure injection: engine out, leak, stuck throttle, guidance loss
- Studies: max payload, parameter sweeps, Monte Carlo
- 4 built-in challenges

### Mission planning
- Flight plans with 12 guidance modes; Python flight computer
- Orbit analysis: per-event orbit log, maneuver planner, predicted path
- **Launch windows**: Lambert porkchop plots (matches the 2001 Mars Odyssey window)
- Powered landing, re-entry calculator, ground track

</td></tr>
<tr><td valign="top">

### Interface
- Dockable mission-control layout, extra 3D & graph windows
- Launch/orbit/follow/first-person cameras
- 4 themes · dark by default · animated splash
- Dark native title bar on Windows

</td><td valign="top">

### Data & quality
- CSV, JSON sessions, Markdown reports, run logs, GIF/MP4 recording
- GPU/CPU rendering choice, Performance mode
- 70+ automated tests · CI on 3 OS × 3 Python versions
- Full docs for users, testers and developers

</td></tr>
</table>

## ⚡ Quick start

**Requirements:** Python 3.10+ · a computer with OpenGL (any GPU from the last ~10 years; CPU rendering also works).

```bash
git clone https://github.com/arshc0der/AstraX.git
cd AstraX
python -m venv venv
venv\Scripts\activate                 # Linux/macOS: source venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Then: **Mission control ▸ "Earth launch to LEO" ▸ Load**, press **Space**. 🎉
More options (standalone builds, editable install, troubleshooting): [docs/INSTALLATION.md](docs/INSTALLATION.md) · 5-minute tour: [docs/QUICKSTART.md](docs/QUICKSTART.md).

<details>
<summary><b>Command-line options</b></summary>

| Command | Effect |
|---|---|
| `python main.py` | start the app |
| `python main.py --no-splash` | skip the animated intro |
| `python main.py --gpu` / `--cpu` | force hardware / software OpenGL for this run |
| `python main.py --gpu-info` | list detected GPUs (no window) |
| `python main.py --diagnostics` | print a system report for bug reports (writes `diagnostics.txt`) |
| `python -m unittest discover -s tests -v` | run all automated tests (no GUI needed) |
| `python tools/benchmark.py` | headless performance benchmark |

</details>

## 📚 Documentation

| I am a... | Start here |
|---|---|
| 👩‍🎓 **User / student** | [Quick start](docs/QUICKSTART.md) → [User guide](docs/USER_GUIDE.md) → [Tutorials](docs/TUTORIALS.md) → [UI reference](docs/UI_REFERENCE.md) → [FAQ](docs/FAQ.md) |
| 👩‍🏫 **Educator** | [Educators' guide](docs/EDUCATORS.md) (lesson plans) → [Tutorials](docs/TUTORIALS.md) |
| 🧪 **Tester / QA** | [Tester hub](docs/tester/README.md) → [Smoke test](docs/tester/SMOKE_TEST.md) → [Manual test cases](docs/tester/MANUAL_TEST_CASES.md) → [Bug reporting](docs/tester/BUG_REPORTING.md) |
| 🧑‍💻 **Developer / contributor** | [Contributing](CONTRIBUTING.md) → [Developer hub](docs/developer/README.md) → [Architecture](docs/ARCHITECTURE.md) → [API reference](docs/API_REFERENCE.md) |
| 🔬 **Researcher** | [Physics & limits](docs/PHYSICS.md) → [Validation](docs/VALIDATION.md) → [Scripting API](docs/SCRIPTING_API.md) → [File formats](docs/FILE_FORMATS.md) |

Everything is indexed in **[docs/README.md](docs/README.md)**.

## 🧮 Accuracy and validation

The engine is checked against analytic and published reference values (see [docs/VALIDATION.md](docs/VALIDATION.md)):

| Check | Result |
|---|---|
| N-body energy conservation, 60 days | relative error < 1e-10 |
| Circular 400 km orbit, 2 orbits (RK4 / DOPRI5 / Verlet) | e < 1e-6, semi-major axis error < 1 m |
| Rocket equation in the simulation | Δv equals `Isp·g₀·ln(m₀/m₁)` to 1e-6 m/s |
| Lambert solver | matches Curtis, *Orbital Mechanics*, Example 5.2 |
| Earth→Mars porkchop | best window = real **2001 Mars Odyssey** window (≈200 days, v∞ ≈ 3.5 km/s) |
| Synodic period Earth–Mars | 779.9 days |
| Re-entry peak deceleration | within 1 % of Allen–Eggers (in its validity limit) |
| Demo rocket ascent | reaches ≈195 × 200 km orbit |

**Limits:** mean-element planet positions (not a perturbed ephemeris), simplified aerodynamics/structure, no attitude dynamics. Read [docs/PHYSICS.md](docs/PHYSICS.md) before relying on any number.

## 🏗️ How it works

```mermaid
flowchart LR
    subgraph UI["ui/  (PyQt6 · pyqtgraph · OpenGL)"]
        MW[MainWindow] --> VP[3D viewport]
        MW --> PN[Panels: designer · mission · telemetry · safety · planner · studies]
    end
    subgraph W["Simulation thread"]
        SW[SimWorker]
    end
    subgraph E["astrax/  (pure Python + NumPy, no Qt)"]
        SIM[Simulation] --- PH[gravity · aero · structure · integrators]
        SIM --- TL[survival · studies · transfer · lambert · reentry]
    end
    MW -- commands --> SW
    SW -- snapshots --> MW
    SW --> SIM
```

The GUI never runs physics; the engine never imports Qt. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 🖥️ Performance and GPU

3D drawing uses the GPU (OpenGL); physics runs on the CPU. AstraX detects your GPU, lets you choose **Auto / GPU / CPU** rendering and prefers the discrete GPU on laptops. See [docs/GRAPHICS_AND_PERFORMANCE.md](docs/GRAPHICS_AND_PERFORMANCE.md).

## ✅ Compatibility

| | Windows 10/11 | Ubuntu / Debian | Fedora / Arch | macOS |
|---|---|---|---|---|
| Run from source | ✅ | ✅ | ✅ | ✅ (Apple Silicon & Intel) |
| Themed native title bar | ✅ | – | – | – |
| Python 3.10 – 3.13 | ✅ | ✅ | ✅ | ✅ |

Full matrix and tested configurations: [docs/tester/COMPATIBILITY_MATRIX.md](docs/tester/COMPATIBILITY_MATRIX.md).

## 🗺️ Roadmap

Planet textures · Phobos/Deimos · rendezvous & docking · gravity-assist planner · perturbation models · batch runner · PySide6 (LGPL) support · plugin API. See [ROADMAP.md](ROADMAP.md) and vote on issues labelled `roadmap`.

## 🤝 Contributing

Contributions of **all kinds** are welcome - code, tests, docs, screenshots, bug reports, lesson plans, scientific review.

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).
2. Pick an issue labelled `good first issue` or `help wanted`, or run the [manual tests](docs/tester/README.md) and report what you find.
3. Open a pull request - CI will check it.

Contributors are listed in [AUTHORS.md](AUTHORS.md). 💙

## 💬 Community and support

- **Questions / ideas / show your work:** [GitHub Discussions](https://github.com/arshc0der/AstraX/discussions)
- **Bugs:** [Issues](https://github.com/arshc0der/AstraX/issues) (run `python main.py --diagnostics` first)
- **Security:** [SECURITY.md](SECURITY.md) (private reporting)
- **More:** [SUPPORT.md](SUPPORT.md)

## ❓ FAQ

<details><summary><b>Is it accurate enough for real missions?</b></summary>No. It is a learning and prototyping tool built on simplified, documented models. See <a href="docs/PHYSICS.md">PHYSICS.md</a>.</details>
<details><summary><b>Why is my GPU at 0%?</b></summary>Only the 3D drawing uses the GPU; physics is CPU-based. On dual-GPU laptops enable <i>Settings ▸ Graphics ▸ Prefer the high-performance GPU</i>. See <a href="docs/GRAPHICS_AND_PERFORMANCE.md">the guide</a>.</details>
<details><summary><b>It crashes or shows a blank 3D view.</b></summary>Update your graphics driver, try <code>python main.py --cpu</code>, then see <a href="docs/TROUBLESHOOTING.md">TROUBLESHOOTING.md</a>.</details>
<details><summary><b>Can I use it in my classroom / paper?</b></summary>Yes (MIT license). See the <a href="docs/EDUCATORS.md">educators' guide</a> and <a href="#-citation">cite AstraX</a>.</details>
<details><summary><b>Can I run the physics without the GUI?</b></summary>Yes - <code>astrax/</code> has no Qt dependency. See the <a href="docs/SCRIPTING_API.md">scripting API</a>.</details>

## 📖 Citation

```bibtex
@software{astrax,
  title   = {AstraX: an open-source spaceflight simulation laboratory},
  author  = {Arsh and contributors},
  year    = {2026},
  version = {4.0.0},
  url     = {https://github.com/arshc0der/AstraX},
  license = {MIT}
}
```
GitHub's **"Cite this repository"** button uses [CITATION.cff](CITATION.cff).

## 📜 License

AstraX source code is released under the **[MIT License](LICENSE)**.

> [!NOTE]
> The UI depends on **PyQt6 (GPLv3 / commercial)**. If you distribute binaries that bundle PyQt6, read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). A PySide6 (LGPL) path is on the roadmap.

## 🙏 Acknowledgements

JPL Solar System Dynamics, the US Standard Atmosphere 1976, H. D. Curtis, Allen & Eggers, Sutton & Graves, J. S. Barrowman, and the PyQt, pyqtgraph, NumPy, Pillow and PyOpenGL communities. Full list: [AUTHORS.md](AUTHORS.md).

<div align="center">

**If AstraX helps you learn or teach spaceflight, please ⭐ the repository and share it!**

[![Star History Chart](https://api.star-history.com/svg?repos=arshc0der/AstraX&type=Date)](https://star-history.com/#arshc0der/AstraX&Date)

</div>
