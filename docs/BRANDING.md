# Branding: logo, splash, icons, theme

## Files
| File | Use |
|---|---|
| `assets/branding/astrax-logo.svg` | master logo (transparent background) |
| `assets/branding/astrax-splash-animated.svg` | master animated splash (SMIL) |
| `assets/branding/astrax-splash-static.svg` | master static splash |
| `assets/logo.ico` / `logo.png` / `logo_16..512.png` | window and taskbar icons (square emblem crop) |
| `assets/logo_full.png` | full logo (About dialog) |
| `assets/splash/f000..f080.jpg` | pre-rendered animated splash frames (81 frames, 20 fps, 960×540) |
| `assets/splash_static.png` | fallback still |

## Why pre-rendered?
Qt's SVG renderer ignores `feGaussianBlur` and `animateMotion`, so the glows and some motion would be wrong. `tools/build_branding.py` renders the SVG in Chromium (exact SMIL timing), steps the animation clock frame by frame and saves JPEGs.

## Theme matching
- The splash background is the **theme colour** (`#0b0f14` for the default dark theme) baked in: the SVG's own blue backdrop is replaced, and a vignette fades the edges into exactly that colour. The splash window uses the theme colour and border.
- The application uses a Fusion style with a palette generated from the theme, plus the stylesheet, so dialogs, menus and scroll areas match.
- On **Windows 10/11** the native title bar/border is coloured from the theme (`ui/winframe.py`, DWM attributes). On Linux/macOS the system draws the title bar.
- The 3D viewport background equals the theme background on dark themes.

## Rebuild after editing the SVGs
```bash
pip install playwright pillow numpy && playwright install chromium
python tools/build_branding.py --bg "#0b0f14"          # other options: --fps --seconds --size --vignette
```
If you change the default theme colour, rebuild with the new `--bg`.
Note: the splash artwork contains baked text ("BUILD 2.0.0 STABLE", "LOADING ORBITAL ENGINE"); edit the SVG and rebuild to change it.

## Splash behaviour
Time-based playback (stays on schedule while modules load), minimum 3.8 s so the intro finishes, last second loops until the window is ready, then a 350 ms fade. Disable with `--no-splash` or Settings ▸ *Show animated splash*.
