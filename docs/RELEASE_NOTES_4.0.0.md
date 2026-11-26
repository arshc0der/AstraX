# AstraX 4.0.0 - "Foundation"

**Release date:** 2026-11-21 · **Type:** feature-complete, professional release (no behaviour change from 3.2.1)

AstraX 4.0 turns the project into a repository ready for a large community: complete documentation for users, testers and developers, automated quality gates, governance and legal clarity - on top of the full simulation laboratory introduced in 3.x.

## Highlights
- **Professional README** with badges, screenshot gallery slots, validation table and architecture diagram.
- **Documentation for three audiences:** users/educators, testers (140 manual test cases, smoke/regression checklists, exploratory charters, performance and compatibility guides) and developers (standards, debugging, CI/CD, packaging, release process, ADR log).
- **CI/CD:** lint, tests on Windows/Linux/macOS × Python 3.10/3.12/3.13, UI import smoke, docs freshness + link check, CodeQL, release automation with checksummed PyInstaller builds.
- **Community files:** Contributing, Code of Conduct, Security policy, Support, Governance, Maintainers, Roadmap, issue/PR templates, CODEOWNERS, Dependabot.
- **Legal clarity:** MIT license plus explicit PyQt6 (GPL/commercial) notice and `THIRD_PARTY_NOTICES`.
- **Tester & maintainer tools:** `--diagnostics` system report, `tools/benchmark.py`, docs link checker, screenshot checker, repo-health tests, `pyproject.toml`, Makefile, pre-commit.

## Everything from 3.x (unchanged code)
Rocket designer with procedural 3D models · survival test with failure/breakup animation · aerodynamics, loads and heating · abort and failure injection · orbit analysis and maneuver planner · Lambert launch-window planner (matches the 2001 Mars Odyssey window) · powered landing · re-entry calculator · studies (max payload, sweeps, Monte Carlo) · challenges · ground track · GPU/CPU rendering choice · animated splash and new branding · themes · extra windows · CSV/session/report export.

## Upgrade notes
- No code or file-format changes: existing rockets, scenarios, planets and sessions load as before.
- New command-line option: `python main.py --diagnostics`.
- Replace the placeholder images in `docs/screenshots/` with real screenshots (see that folder's README).
- If you fork: run `python tools/set_repo_slug.py yourname/YourRepo` to retarget badges and links.

## Known issues
See [tester/KNOWN_ISSUES.md](tester/KNOWN_ISSUES.md). The GUI is verified manually; please run the [smoke test](tester/SMOKE_TEST.md) and report results.

## Thanks
To everyone who tests, documents, teaches with, and contributes to AstraX. 💙
