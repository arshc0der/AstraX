# Packaging

## Run from source (default distribution)
`git clone` + `pip install -r requirements.txt` + `python main.py`.

## Editable / wheel
`pip install -e .` installs `astrax`, `ui` and the `astrax` console command (`main:main`). **Assets are loaded relative to `main.py`**, so keep the repository folder when installing editable. A fully relocatable wheel would require moving `assets/` into the package (tracked in the roadmap).

## Standalone apps with PyInstaller
```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --windowed --name AstraX --icon assets/logo.ico --add-data "assets;assets" --collect-all pyqtgraph main.py     # Windows (use ':' on Linux/macOS)
```
Output: `dist/AstraX/`. `make build` picks the correct separator. The release workflow builds all three OSes and publishes checksums.

### Checklist for a good bundle
- Includes `assets/` (logo, splash frames) - verify the splash shows.
- Starts on a clean VM without Python.
- `--cpu` flag still works (software OpenGL DLL bundled by PyQt6).
- Antivirus false positives: sign the binary (Windows) / notarise (macOS) if distributing widely.

## Licensing of bundles
PyQt6 is GPL/commercial; read [THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md) before redistributing.

## Linux packages (ideas)
AppImage or Flatpak; Debian/Fedora packaging welcome as community contributions.
