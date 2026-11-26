# Documentation guide

## Audiences
| Audience | Docs | Tone |
|---|---|---|
| Users/students | QUICKSTART, USER_GUIDE, TUTORIALS, UI_REFERENCE, FAQ, TROUBLESHOOTING, GLOSSARY, EDUCATORS | friendly, step-by-step, explain terms |
| Testers | `docs/tester/` | precise, checklists, expected values |
| Developers | `docs/developer/`, ARCHITECTURE, DEVELOPER_GUIDE, API_REFERENCE | concise, code-oriented |
| Researchers | PHYSICS, VALIDATION, SCRIPTING_API, FILE_FORMATS | rigorous, with sources and limitations |

## Rules
- One topic per page; link instead of copying. Put new pages in [../README.md](../README.md).
- Every command/value in a doc must actually work (CI runs the link check; testers run QUICKSTART).
- Use **relative links**; run `python tools/check_docs_links.py`.
- Use tables for reference, numbered steps for procedures, callouts (`> **Note**`) sparingly.
- State units. State limitations next to claims.
- Screenshots: PNG, 1600×900, dark theme, same file names ([docs/screenshots/README.md](../screenshots/README.md)).

## Generated documents - do not edit by hand
| File | Generator |
|---|---|
| `docs/API_REFERENCE.md`, `FILE_FORMATS.md`, `VALIDATION.md` | `python tools/gen_docs.py` |
| `docs/tester/MANUAL_TEST_CASES.md`, `test_cases.csv`, `SMOKE_TEST.md`, `REGRESSION_CHECKLIST.md` | `python tools/gen_test_cases.py` |
CI fails if the generated files are stale.

## Style
Short sentences; active voice; second person for tutorials ("Press Space"); consistent names (*Rocket designer*, *Flight safety*, *Launch windows*); keep UI labels exactly as in the app.

## Translating
Create `docs/<lang>/` with translated QUICKSTART/USER_GUIDE first; keep file names; note the English version it tracks. Translators are credited in AUTHORS.md.

## Checklist for doc PRs
Spelling · links · commands tested · screenshots current · no private paths · index updated.
