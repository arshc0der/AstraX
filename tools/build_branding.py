"""Build the raster branding assets from the SVG originals in assets/branding/.   (developer tool - not needed to run AstraX)

    pip install playwright pillow && playwright install chromium
    python tools/build_branding.py [--bg "#0b0f14"] [--fps 20] [--seconds 4.0] [--size 960]

Why raster? Qt's SVG renderer ignores blur filters and animateMotion, so the glow/animation would look wrong. Chromium renders the SVG
(SMIL animation included) exactly; we step the animation clock frame by frame and bake the THEME background colour into the frames so
the splash blends with the application window.
"""
import argparse, io, os, re, sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BR, OUT, SPL = (os.path.join(ROOT, "assets", p) for p in ("branding", "", "splash"))
BG_STOPS = re.compile(r'(<radialGradient id="bg"[^>]*>)(.*?)(</radialGradient>)', re.S)


def themed(svg: str, bg: str) -> str:
    """Replace the SVG's own blue backdrop gradient by the solid theme colour (nebula/stars/HUD stay)."""
    return BG_STOPS.sub(lambda m: f'{m.group(1)}<stop offset="0" stop-color="{bg}"/><stop offset="1" stop-color="{bg}"/>{m.group(3)}', svg, count=1)


def page(svg: str, bg: str, w: int, h: int) -> str:
    svg = svg.replace("<svg ", f'<svg id="S" width="{w}" height="{h}" style="display:block" ', 1)
    svg = re.sub(r'(<svg id="S"[^>]*?) width="1280" height="720"', r"\1", svg, count=1)
    return f"<html><body style='margin:0;background:{bg};overflow:hidden'>{svg}</body></html>"


def vignette(img: Image.Image, bg: str, strength: float) -> Image.Image:
    """Fade the frame edges into the theme background colour so the splash blends with the application window."""
    if strength <= 0: return img
    w, h = img.size; yy, xx = np.mgrid[0:h, 0:w]; d = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    t = np.clip((d - 0.72) / (1.08 - 0.72), 0, 1); t = t * t * (3 - 2 * t); al = (t * strength)[..., None]
    col = np.array([int(bg[i:i + 2], 16) for i in (1, 3, 5)], float)
    return Image.fromarray((np.asarray(img, float) * (1 - al) + col * al).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--bg", default="#0b0f14"); ap.add_argument("--fps", type=int, default=20); ap.add_argument("--seconds", type=float, default=4.0); ap.add_argument("--size", type=int, default=960); ap.add_argument("--vignette", type=float, default=0.92, help="edge fade into the theme colour (0 = off)")
    a = ap.parse_args(); W = a.size; H = round(W * 9 / 16)
    os.makedirs(SPL, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        # ---- animated splash -> JPEG frames
        svg = themed(open(os.path.join(BR, "astrax-splash-animated.svg"), encoding="utf-8").read(), a.bg)
        pg = b.new_page(viewport={"width": W, "height": H}); pg.set_content(page(svg, a.bg, W, H)); pg.wait_for_timeout(400); pg.evaluate("()=>document.getElementById('S').pauseAnimations()")
        n = int(a.seconds * a.fps) + 1
        for f in os.listdir(SPL):
            if f.endswith(".jpg"): os.remove(os.path.join(SPL, f))
        for i in range(n):
            pg.evaluate("t=>document.getElementById('S').setCurrentTime(t)", i / a.fps); pg.wait_for_timeout(35)
            vignette(Image.open(io.BytesIO(pg.screenshot())).convert("RGB"), a.bg, a.vignette).save(os.path.join(SPL, f"f{i:03d}.jpg"), quality=88, optimize=True)
        # last frame as a static fallback
        vignette(Image.open(io.BytesIO(pg.screenshot())).convert("RGB"), a.bg, a.vignette).save(os.path.join(OUT, "splash_static.png"), optimize=True)
        # ---- logo (transparent background)
        logo = open(os.path.join(BR, "astrax-logo.svg"), encoding="utf-8").read()
        pg = b.new_page(viewport={"width": 1280, "height": 720}); pg.set_content(page(logo, "transparent", 1280, 720).replace("background:transparent", "background:transparent")); pg.wait_for_timeout(300)
        full = Image.open(io.BytesIO(pg.screenshot(omit_background=True))).convert("RGBA"); full.save(os.path.join(OUT, "logo_full.png"), optimize=True)
        b.close()
    # ---- square emblem icon
    s = 500; cx, cy = 640, 285; icon = full.crop((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2))
    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    for z in sizes: icon.resize((z, z), Image.LANCZOS).save(os.path.join(OUT, f"logo_{z}.png"), optimize=True)
    icon.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT, "logo.ico"), sizes=[(z, z) for z in (16, 24, 32, 48, 64, 128, 256)])
    icon.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "logo.png"), optimize=True)
    print(f"frames: {n} @ {a.fps} fps, {W}x{H}; icons: {sizes}")


if __name__ == "__main__":
    main()
