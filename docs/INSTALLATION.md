# Installation guide

## Requirements
| | Minimum | Recommended |
|---|---|---|
| OS | Windows 10, Ubuntu 22.04, macOS 12 | Windows 11, Ubuntu 24.04, macOS 14 |
| Python | 3.10 | 3.12 |
| CPU | any 2-core | 4+ cores (physics is CPU-bound) |
| RAM | 4 GB | 8 GB |
| Graphics | OpenGL 2.1 (or CPU rendering) | any dedicated or modern integrated GPU + current driver |
| Disk | 200 MB for the app + dependencies | |

## Option A - run from source (all platforms, recommended)
```bash
git clone https://github.com/arshc0der/AstraX.git
cd AstraX
python -m venv venv
```
Activate the environment:
| Shell | Command |
|---|---|
| Windows PowerShell | `venv\Scripts\Activate.ps1` |
| Windows CMD | `venv\Scripts\activate.bat` |
| Linux / macOS | `source venv/bin/activate` |

Then:
```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```
> **PowerShell blocks the script?** run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
> **`pip.exe` blocked by a security policy?** always use `python -m pip ...`.

## Option B - editable install (developers)
```bash
python -m pip install -e ".[dev]"
astrax                  # console command, same as: python main.py
```
Keep the repository folder: the app loads `assets/` from it.

## Option C - standalone app (no Python needed)
Download `AstraX-windows.zip`, `AstraX-linux.zip` or `AstraX-macos.zip` from the [Releases](https://github.com/arshc0der/AstraX/releases) page, unzip and run `AstraX`. Verify the checksum with the attached `.sha256` file. (Binaries bundle PyQt6 - see [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md).)
Build your own: `make build` or see [developer/PACKAGING.md](developer/PACKAGING.md).

## Platform notes
### Windows
- Install Python from python.org and tick **Add python.exe to PATH**.
- Laptops with two GPUs: *Tools ▸ Settings ▸ Graphics ▸ Prefer the high-performance GPU*, restart.
- If a Qt DLL is blocked by an "Application Control" policy, ask your administrator to allow the project's `venv` folder.

### Linux
Install the system libraries Qt needs if the app fails to start (`xcb` plugin errors):
```bash
# Debian / Ubuntu
sudo apt install libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libdbus-1-3
# Fedora
sudo dnf install mesa-libGL libxkbcommon-x11 xcb-util-cursor
```
Wayland users: if the window misbehaves, run `QT_QPA_PLATFORM=xcb python main.py`.
Dual-GPU laptops: tick *Prefer the high-performance GPU* (sets PRIME offload variables).

### macOS
Install Python 3.12 (python.org or Homebrew). OpenGL is deprecated but works with PyQt6. If the 3D view is blank on a new macOS release, run `python main.py --cpu` and report it with `--diagnostics`.

## First run checklist
1. `python main.py --diagnostics` prints versions and GPUs (nothing opens).
2. `python main.py` opens the splash, then the main window.
3. Load *Earth launch to LEO* and press **Space**.

## Updating
```bash
git pull
python -m pip install -r requirements.txt --upgrade
```
Settings are kept (stored by Qt). Rocket/scenario JSON files stay compatible (format tags, defaults for new fields).

## Uninstalling
Delete the project folder and its `venv`. Settings live in the Qt settings store (Windows registry key `HKCU\Software\AstraX`, Linux `~/.config/AstraX`, macOS `~/Library/Preferences`).

## Verify your installation
```bash
python -m pip install pytest   # optional
python -m unittest discover -s tests -v      # engine tests, no GUI
```

Problems? [TROUBLESHOOTING](TROUBLESHOOTING.md).
