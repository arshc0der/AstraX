"""List which screenshots are still placeholders (placeholders carry a hidden PNG tag 'astrax_placeholder').   python tools/check_screenshots.py"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); D = os.path.join(ROOT, "docs", "screenshots")


def status():
    from PIL import Image
    readme = open(os.path.join(D, "README.md"), encoding="utf-8").read(); out = []
    for n in re.findall(r"\| `([\w-]+\.png)` \|", readme):
        p = os.path.join(D, n)
        if not os.path.exists(p): out.append((n, "missing")); continue
        with Image.open(p) as im: out.append((n, "placeholder" if im.info.get("astrax_placeholder") else "real"))
    return out


def main():
    st = status()
    for n, s in st: print(f"{s:<12}{n}")
    real = sum(1 for _, s in st if s == "real"); print(f"\n{real}/{len(st)} real screenshots; {len(st) - real} still to upload"); return 0


if __name__ == "__main__":
    sys.exit(main())
