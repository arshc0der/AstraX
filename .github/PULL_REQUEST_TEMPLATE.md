## What does this PR do?
<!-- One or two sentences. Link the issue: Fixes #123 -->

## Type of change
- [ ] Bug fix  - [ ] Feature  - [ ] Physics/model change  - [ ] UI change  - [ ] Documentation  - [ ] Tests  - [ ] Refactor / performance  - [ ] CI / tooling

## How was it tested?
- [ ] `python -m unittest discover -s tests` passes
- [ ] I added/updated tests (physics changes need an analytic/reference test)
- [ ] I ran the app (`python main.py`) and tried the change - OS: ____
- [ ] Manual test cases checked: TC-___

## Screenshots / recordings (UI changes)
<!-- drag and drop images here -->

## Documentation
- [ ] Updated the relevant docs (and `docs/PHYSICS.md` for models)
- [ ] Re-generated generated docs: `python tools/gen_docs.py`
- [ ] Added a line to `CHANGELOG.md` under **Unreleased**

## Checklist
- [ ] `astrax/` has no Qt imports; `ui/` has no physics
- [ ] No Qt method names overridden; no GL rebuilds in `paintGL`
- [ ] JSON file changes are backwards compatible (new fields have defaults)
- [ ] I have read [CONTRIBUTING.md](../CONTRIBUTING.md) and agree to the MIT license
