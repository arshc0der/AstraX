"""Repository health: required files, version consistency, links, docs and screenshots map. No GUI needed."""
import csv, os, re, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


def read(*p): return open(os.path.join(ROOT, *p), encoding="utf-8").read()


class TestRequiredFiles(unittest.TestCase):
    FILES = ["README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "SUPPORT.md", "GOVERNANCE.md", "MAINTAINERS.md", "ROADMAP.md", "AUTHORS.md",
             "THIRD_PARTY_NOTICES.md", "CITATION.cff", "pyproject.toml", "requirements.txt", "requirements-dev.txt", "Makefile", ".editorconfig", ".gitattributes", ".gitignore",
             ".pre-commit-config.yaml", "MANIFEST.in", ".github/PULL_REQUEST_TEMPLATE.md", ".github/CODEOWNERS", ".github/dependabot.yml", ".github/workflows/ci.yml", ".github/workflows/release.yml",
             ".github/workflows/codeql.yml", ".github/ISSUE_TEMPLATE/bug_report.yml", ".github/ISSUE_TEMPLATE/feature_request.yml", ".github/ISSUE_TEMPLATE/config.yml",
             "docs/README.md", "docs/INSTALLATION.md", "docs/QUICKSTART.md", "docs/USER_GUIDE.md", "docs/TUTORIALS.md", "docs/TROUBLESHOOTING.md", "docs/FAQ.md", "docs/PHYSICS.md",
             "docs/tester/README.md", "docs/tester/MANUAL_TEST_CASES.md", "docs/tester/SMOKE_TEST.md", "docs/tester/BUG_REPORTING.md", "docs/developer/README.md", "docs/developer/CODING_STANDARDS.md",
             "assets/logo.ico", "assets/logo.png", "assets/social-preview.png", "assets/banner.png", "main.py"]
    def test_files_exist(self):
        missing = [f for f in self.FILES if not os.path.exists(os.path.join(ROOT, f))]; self.assertEqual(missing, [])
    def test_license_is_mit(self): self.assertIn("MIT License", read("LICENSE"))
    def test_splash_frames_present(self): self.assertGreaterEqual(len([f for f in os.listdir(os.path.join(ROOT, "assets", "splash")) if f.endswith(".jpg")]), 60)


class TestVersionConsistency(unittest.TestCase):
    def test_versions_match(self):
        import astrax
        v = astrax.__version__
        self.assertRegex(v, r"^\d+\.\d+\.\d+")
        self.assertIn(f'version = "{v}"', read("pyproject.toml")); self.assertIn(f"version: {v}", read("CITATION.cff"))
        self.assertRegex(read("CHANGELOG.md"), rf"(?m)^## \[?{re.escape(v)}\]?")
        self.assertIn(f"version = {{{v}}}", read("README.md"))
    def test_dependencies_match_requirements(self):
        names = lambda lines: {re.split(r"[<>=\[ ]", l.strip().strip('",'))[0].lower() for l in lines if l.strip() and not l.strip().startswith("#")}
        req = names(read("requirements.txt").splitlines())
        py = read("pyproject.toml"); block = py.split("dependencies = [", 1)[1].split("]", 1)[0]
        self.assertEqual(req, names(block.splitlines()))


class TestDocs(unittest.TestCase):
    def test_markdown_links_resolve(self):
        from tools.check_docs_links import check
        bad = check(); self.assertEqual(bad, [], f"broken links: {bad[:10]}")
    def test_screenshots_listed_and_exist(self):
        listed = re.findall(r"\| `([\w-]+\.png)` \|", read("docs", "screenshots", "README.md")); self.assertGreaterEqual(len(listed), 15)
        for n in listed: self.assertTrue(os.path.exists(os.path.join(ROOT, "docs", "screenshots", n)), n)
        readme = read("README.md")
        for n in re.findall(r"docs/screenshots/([\w-]+\.png)", readme): self.assertIn(n, listed)
    def test_manual_test_cases_consistent(self):
        rows = list(csv.DictReader(open(os.path.join(ROOT, "docs", "tester", "test_cases.csv"), encoding="utf-8")))
        ids = [r["ID"] for r in rows]; self.assertEqual(len(ids), len(set(ids))); self.assertGreaterEqual(len(ids), 100)
        md = read("docs", "tester", "MANUAL_TEST_CASES.md"); self.assertTrue(all(i in md for i in ids))
        self.assertTrue({r["Priority"] for r in rows} <= {"P1", "P2", "P3"})
    def test_docs_index_links_every_doc(self):
        idx = read("docs", "README.md")
        for d, _, files in os.walk(os.path.join(ROOT, "docs")):
            if "screenshots" in d or "examples" in d: continue
            for f in files:
                if f.endswith(".md") and f != "README.md": self.assertIn(f, idx, f"{f} is not linked from docs/README.md")
    def test_readme_core_sections(self):
        r = read("README.md")
        for s in ("Quick start", "Features", "Documentation", "Contributing", "License", "FAQ", "Citation"): self.assertIn(s, r)
    def test_every_public_flag_documented(self):
        for flag in ("--no-splash", "--gpu-info", "--diagnostics", "--cpu", "--gpu"): self.assertIn(flag, read("README.md"))


class TestTools(unittest.TestCase):
    def test_release_notes_extract(self):
        from tools.release_notes import section
        self.assertIn("Foundation", section("4.0.0")); self.assertIn("Added", section("4.0.0"))
    def test_diagnostics_report_runs(self):
        from tools.diagnostics import report
        text = report(); self.assertIn("AstraX", text); self.assertIn("Python", text); self.assertNotIn("FAILED", text)
    def test_screenshot_status_runs(self):
        from tools.check_screenshots import status
        st = status(); self.assertTrue(all(s in ("real", "placeholder", "missing") for _, s in st)); self.assertFalse(any(s == "missing" for _, s in st))


if __name__ == "__main__":
    unittest.main()
