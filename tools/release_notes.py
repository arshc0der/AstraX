"""Print the CHANGELOG section for one version (used by the release workflow).   python tools/release_notes.py 4.0.0"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def section(version: str) -> str:
    text = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
    m = re.search(rf"^## \[?{re.escape(version)}\]?.*?$(.*?)(?=^## |\Z)", text, flags=re.S | re.M)
    return (m.group(1).strip() if m else f"Release {version}") + "\n"


if __name__ == "__main__":
    print(section(sys.argv[1] if len(sys.argv) > 1 else "Unreleased"))
