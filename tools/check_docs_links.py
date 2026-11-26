"""Check that every relative link/image in the Markdown files resolves to a file.   python tools/check_docs_links.py"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKIP_DIRS = {"legacy", "venv", ".venv", ".git", "node_modules", "Testing", "build", "dist"}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
GITHUB_REL = re.compile(r"^(\.\./)+(issues|discussions|tree|blob|security|pulls|actions|releases|wiki)")


def md_files():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"): yield os.path.join(d, f)


def check():
    bad = []
    for path in md_files():
        text = open(path, encoding="utf-8").read(); text = re.sub(r"```.*?```", "", text, flags=re.S)
        for m in LINK.finditer(text):
            tgt = m.group(1)
            if re.match(r"^(https?:|mailto:|#|tel:)", tgt) or GITHUB_REL.match(tgt): continue
            tgt = tgt.split("#")[0]
            if not tgt: continue
            full = os.path.normpath(os.path.join(os.path.dirname(path), tgt))
            if not os.path.exists(full): bad.append((os.path.relpath(path, ROOT), m.group(1)))
    return bad


if __name__ == "__main__":
    bad = check()
    for p, t in bad: print(f"BROKEN LINK  {p}: {t}")
    print(f"{len(bad)} broken link(s)"); sys.exit(1 if bad else 0)
