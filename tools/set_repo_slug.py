"""Replace the default GitHub slug 'arshc0der/AstraX' everywhere (badges, links, citation) with yours.
    python tools/set_repo_slug.py yourname/YourRepo
"""
import os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OLD = "arshc0der/AstraX"
EXT = (".md", ".yml", ".yaml", ".toml", ".cff", ".txt", ".json")


def main():
    if len(sys.argv) != 2 or "/" not in sys.argv[1]: print(__doc__); return 1
    new = sys.argv[1].strip(); n = 0
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in {".git", "venv", ".venv", "legacy"}]
        for f in files:
            if f.endswith(EXT) or f in ("CODEOWNERS",):
                p = os.path.join(d, f)
                try: s = open(p, encoding="utf-8").read()
                except Exception: continue
                if OLD in s: open(p, "w", encoding="utf-8").write(s.replace(OLD, new)); n += 1
    print(f"updated {n} file(s): {OLD} -> {new}"); return 0


if __name__ == "__main__":
    sys.exit(main())
