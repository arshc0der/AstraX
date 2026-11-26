# Release checklist

Copy into the release PR/issue and tick every box.

## Code freeze
- [ ] CI green on `main` (lint, tests 3 OS × 3 Python, UI import smoke, docs)
- [ ] No open S1/S2 defects; known issues listed in [KNOWN_ISSUES](KNOWN_ISSUES.md)
- [ ] Dependencies reviewed (Dependabot PRs merged or deferred with reason)

## Version and documents
- [ ] Version bumped in `astrax/__init__.py`, `pyproject.toml`, `CITATION.cff` (repo health test checks equality)
- [ ] `CHANGELOG.md`: *Unreleased* moved under the new version with date
- [ ] Release notes drafted (`docs/RELEASE_NOTES_<version>.md`)
- [ ] `python tools/gen_docs.py` and `python tools/gen_test_cases.py` re-run and committed
- [ ] `python tools/check_docs_links.py` → 0 broken
- [ ] Screenshots current (`python tools/check_screenshots.py`)

## Testing
- [ ] Smoke test passed on Windows, Linux, macOS
- [ ] Regression checklist (all P1) passed on ≥ 2 OS
- [ ] Performance scenarios P-2/P-3/P-4 within 25 % of the previous release
- [ ] Clean-machine install follows QUICKSTART exactly
- [ ] GPU and CPU rendering both verified
- [ ] Packaged binaries start (Windows, Linux, macOS) and show the splash and logo

## Legal and security
- [ ] LICENSE and [THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md) current (note PyQt6 for binaries)
- [ ] No secrets, personal paths or large binaries committed
- [ ] SECURITY.md supported-versions table updated

## Publish
- [ ] Tag `vX.Y.Z` → release workflow builds artifacts + checksums
- [ ] Release page: notes, pre-release flag correct, checksums attached
- [ ] Announce in Discussions; update the social preview if the logo changed
- [ ] Verify downloads on a fresh machine
- [ ] Open the next *Unreleased* section in the changelog
