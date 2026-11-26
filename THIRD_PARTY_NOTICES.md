# Third-party notices

AstraX's own source code is released under the **MIT License** ([LICENSE](LICENSE)). It depends on the following third-party software, each under its own license.

| Component | Used for | License |
|---|---|---|
| **PyQt6** (Riverbank Computing) | desktop UI | **GPL v3** or a commercial license |
| Qt 6 (The Qt Company) | UI toolkit used by PyQt6 | LGPL v3 / GPL / commercial |
| pyqtgraph | graphs, 3D scene | MIT |
| NumPy | numerical computing | BSD-3-Clause |
| PyOpenGL | OpenGL bindings | BSD-style |
| Pillow | images, GIF recording | HPND (PIL license) |
| matplotlib (optional) | PNG graphs in reports | PSF-based (Matplotlib license) |
| PyInstaller (build only) | standalone apps | GPL v2+ with a bootloader exception |
| Playwright (developer tool only) | rendering the logo/splash | Apache-2.0 |

## Important: PyQt6 licensing
PyQt6 is available under **GPLv3 or a commercial license**. The AstraX *source* is MIT, so you may use it under MIT terms. However, if you **distribute a combined binary** (for example a PyInstaller build that bundles PyQt6), that distribution must comply with the GPLv3 for the PyQt6 portion (provide corresponding source, license text, etc.) unless you hold a commercial PyQt license. This is not legal advice; check with a qualified person before redistributing binaries commercially.

Maintainers' plan: evaluate a migration to **PySide6** (LGPL), which would remove this constraint (tracked in [ROADMAP.md](ROADMAP.md)).

## Data
Reference constants and orbital elements are public scientific data (see [docs/PHYSICS.md](docs/PHYSICS.md) and [AUTHORS.md](AUTHORS.md)). The example rockets are **illustrative** and are not official models of any real vehicle.

## Trademarks
Names of real vehicles or companies mentioned in documentation are trademarks of their owners and are used for descriptive purposes only.
