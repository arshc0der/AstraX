# Release process

Versioning: **Semantic Versioning** (`MAJOR.MINOR.PATCH`, optional `-dev`/`-rc.N`). MAJOR = breaking change in file formats/API; MINOR = features; PATCH = fixes.

## Steps
1. **Branch** `release/X.Y.Z` from `main`.
2. **Version**: set the same number in `astrax/__init__.py`, `pyproject.toml`, `CITATION.cff` (`version`, `date-released`).
3. **Changelog**: rename *Unreleased* to `## X.Y.Z - YYYY-MM-DD`; create a fresh *Unreleased*.
4. **Docs**: `python tools/gen_docs.py`, `python tools/gen_test_cases.py`, `python tools/check_docs_links.py`; write `docs/RELEASE_NOTES_X.Y.Z.md`; refresh screenshots.
5. **Test**: follow [tester/RELEASE_CHECKLIST.md](../tester/RELEASE_CHECKLIST.md) (smoke on all OS, regression on ≥ 2).
6. **PR** into `main`; CI green; approval.
7. **Tag**: `git tag -a vX.Y.Z -m "AstraX X.Y.Z" && git push origin vX.Y.Z`.
8. **Workflow** builds binaries, checksums, sdist/wheel and creates the GitHub Release from the changelog section.
9. **Verify** downloads on a fresh machine; fix forward with a patch release if needed.
10. **Announce** in Discussions; update the roadmap.

## Hotfixes
Branch from the tag → fix + test → bump PATCH → same steps (shortened checklist: smoke + affected area).

## Deprecation policy
Public engine API and file formats: announce in the changelog one MINOR release ahead; formats stay readable (defaults for new fields, `astrax_format` tag versions).

## Release notes template
```
## Highlights  - 3 bullets
## New / Improved / Fixed  - grouped
## Known issues  - link KNOWN_ISSUES
## Upgrade notes  - anything users must do
## Thanks  - contributors
```
