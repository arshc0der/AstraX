# CI/CD

| Workflow | File | Trigger | Does |
|---|---|---|---|
| **CI** | `.github/workflows/ci.yml` | push to `main`, every PR | ruff lint + compile; engine & repository tests on Ubuntu/Windows/macOS × Python 3.10/3.12/3.13; UI import smoke (offscreen Qt, constructs `MainWindow`); docs freshness + link check |
| **Release** | `release.yml` | tag `v*` or manual | tests, PyInstaller builds (Windows/Linux/macOS) + SHA-256, sdist/wheel, GitHub Release with notes from `CHANGELOG.md` (pre-release if the tag contains `dev`/`rc`/`beta`) |
| **CodeQL** | `codeql.yml` | push/PR/weekly | security analysis of the Python code |
| **Stale** | `stale.yml` | daily | marks/closes inactive issues (exempt: roadmap, security, pinned) |
| **Labeler** | `labeler.yml` | PRs | applies labels by changed paths |
| **Dependabot** | `dependabot.yml` | weekly/monthly | dependency update PRs |

## Reproduce CI locally
```bash
ruff check . && python -m compileall -q astrax ui tools main.py
python -m unittest discover -s tests -v
python tools/gen_docs.py && git diff --exit-code docs/API_REFERENCE.md docs/FILE_FORMATS.md docs/VALIDATION.md
python tools/check_docs_links.py
```

## Protected branch settings (recommended)
Require PRs and the **CI** checks (lint, tests, docs, ui-import-smoke), 1 approving review, linear history (squash), dismiss stale approvals, require conversation resolution.

## Secrets
None required. Release uses the built-in `GITHUB_TOKEN`.

## Adding a CI job
Keep jobs short; no network except package installs; headless only. Update this page and `docs/tester/TESTING_GUIDE.md`.
