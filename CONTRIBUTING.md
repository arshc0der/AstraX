# Contributing to AstraX

Thank you for helping! AstraX welcomes code, tests, documentation, bug reports, screenshots, translations of docs, scientific review and teaching material. **You do not need to be a programmer to contribute** - testers and educators are just as valuable.

## Ways to contribute
| You are... | You can... | Start here |
|---|---|---|
| A user | report bugs, suggest features, share scenarios/rockets | [Issues](../../issues), [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| A tester | run the manual test suite, report results | [docs/tester/README.md](docs/tester/README.md) |
| An educator | share lesson plans, tutorials | [docs/EDUCATORS.md](docs/EDUCATORS.md) |
| A scientist/engineer | review models, add validation cases | [docs/PHYSICS.md](docs/PHYSICS.md), [docs/VALIDATION.md](docs/VALIDATION.md) |
| A developer | fix bugs, add features, improve performance | below + [docs/developer/README.md](docs/developer/README.md) |
| A writer/designer | improve docs, screenshots, icons | [docs/developer/DOCUMENTATION_GUIDE.md](docs/developer/DOCUMENTATION_GUIDE.md) |

## Quick start for developers
```bash
git clone https://github.com/arshc0der/AstraX.git && cd AstraX
python -m venv venv && venv\Scripts\activate            # Linux/macOS: source venv/bin/activate
python -m pip install -r requirements-dev.txt
pre-commit install
python -m unittest discover -s tests -v                  # ~3 minutes, no GUI needed
python main.py                                           # run the app
```

## Workflow
1. **Search** existing issues/discussions. For non-trivial work, open an issue first so we agree on the approach.
2. **Fork**, create a branch: `feat/<topic>`, `fix/<topic>`, `docs/<topic>`, `test/<topic>`.
3. **Change** the code (see standards below), **add tests**, **update docs**.
4. **Check locally**: `make test lint docs` (or the commands inside).
5. **Commit** with [Conventional Commits](https://www.conventionalcommits.org/): `feat(sim): add staging delay`, `fix(ui): grid size order`, `docs: add tutorial`.
6. **Open a pull request** using the template; link the issue; describe testing (including screenshots for UI changes).
7. A maintainer reviews. CI must pass. We squash-merge.

## Standards (summary - full version: [docs/developer/CODING_STANDARDS.md](docs/developer/CODING_STANDARDS.md))
- **Layering:** `astrax/` has no Qt/OpenGL imports; `ui/` has no physics.
- **Units:** SI internally; unit suffixes in names (`_m`, `_s`, `_kg`, `_deg`).
- **Physics changes need a test against an analytic/reference value** and an entry in `docs/PHYSICS.md` (assumptions, limitations, validation).
- **Never present unvalidated results as research-grade.**
- **Threading:** never run physics on the GUI thread; use `FuncWorker` or `worker.command(...)`.
- **Qt:** do not override Qt method names (`update`, `move`, `result`...); never rebuild GL items inside `paintGL`.
- **Docs:** generated docs (`API_REFERENCE`, `FILE_FORMATS`, `VALIDATION`) are produced by `python tools/gen_docs.py`; do not edit them by hand.
- **Backwards compatibility:** JSON files carry a format tag; new fields must have defaults.

## What a good PR contains
- A focused change; tests; updated docs/changelog (`CHANGELOG.md` under *Unreleased*); screenshots for visible UI changes; no unrelated reformatting.

## Reporting bugs well
Run `python main.py --diagnostics`, attach the output, the log file (`logs/`), steps to reproduce, expected vs actual, and a screenshot. See [docs/tester/BUG_REPORTING.md](docs/tester/BUG_REPORTING.md).

## Scientific contributions
Add the equations, the source (paper/book/dataset with units and epoch), the limitations, and at least one validation test. See [docs/developer/ADDING_PHYSICS.md](docs/developer/ADDING_PHYSICS.md).

## Licensing
By contributing you agree your work is licensed under the project's [MIT License](LICENSE). Do not paste code you do not have the right to relicense. Note the [third-party notices](THIRD_PARTY_NOTICES.md) (PyQt6).

## Code of Conduct
Participation requires following the [Code of Conduct](CODE_OF_CONDUCT.md).

## Recognition
Everyone who contributes is listed in [AUTHORS.md](AUTHORS.md) (add yourself in your first PR!).
