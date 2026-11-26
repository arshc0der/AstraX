# Compatibility matrix

Maintainers and testers update this table in pull requests. Legend: ✅ works · ⚠️ works with notes · ❌ fails · ❔ untested.

## Operating systems and Python
| OS | 3.10 | 3.11 | 3.12 | 3.13 | Notes |
|---|---|---|---|---|---|
| Windows 11 | ❔ | ❔ | ✅ | ❔ | developer machines; themed title bar |
| Windows 10 | ❔ | ❔ | ❔ | ❔ | themed title bar from build 1809 |
| Ubuntu 22.04 / 24.04 | ❔ | ❔ | ❔ | ❔ | needs xcb libs ([INSTALLATION](../INSTALLATION.md)) |
| Fedora / Arch | ❔ | ❔ | ❔ | ❔ | |
| macOS 12–15 (Apple Silicon) | ❔ | ❔ | ❔ | ❔ | OpenGL deprecated but works |
| macOS (Intel) | ❔ | ❔ | ❔ | ❔ | |
| **Automated (CI engine tests)** | ✅ | – | ✅ | ✅ | ubuntu, windows, macos |

## Graphics
| GPU / driver | Status | Notes |
|---|---|---|
| NVIDIA GeForce (proprietary driver) | ❔ | dual-GPU: enable *Prefer high-performance GPU* |
| AMD Radeon (Adrenalin / Mesa) | ❔ | |
| Intel UHD / Iris / Arc | ❔ | |
| Apple M-series | ❔ | |
| Software OpenGL (`--cpu`, llvmpipe) | ⚠️ | works, slower; use Performance mode |
| Virtual machine GPUs | ⚠️ | often software rendering |
| Remote desktop (RDP) | ⚠️ | may fall back to GDI Generic / software |

## Display
| Setup | Status |
|---|---|
| 1366×768 | ⚠️ panels scroll |
| 1920×1080 | ✅ |
| 4K, 150–200 % scaling | ❔ (use font size / `QT_SCALE_FACTOR`) |
| Multi-monitor, floating docks | ❔ |

## How to contribute a row
Run `python main.py --diagnostics`, run the [smoke test](SMOKE_TEST.md), and open a PR changing ❔ to ✅/⚠️/❌ with a one-line note (and an issue link for ❌).
