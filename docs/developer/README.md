# Developer hub

| Topic | Document |
|---|---|
| How to contribute (workflow, PR rules) | [../../CONTRIBUTING.md](../../CONTRIBUTING.md) |
| Code structure and data flow | [../ARCHITECTURE.md](../ARCHITECTURE.md) |
| Recipes: add a body / guidance mode / failure / panel | [../DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) |
| Coding standards | [CODING_STANDARDS.md](CODING_STANDARDS.md) |
| Adding or changing physics correctly | [ADDING_PHYSICS.md](ADDING_PHYSICS.md) |
| Debugging (Qt, OpenGL, threads, numerics) | [DEBUGGING.md](DEBUGGING.md) |
| CI/CD workflows | [CI_CD.md](CI_CD.md) |
| Packaging (PyInstaller, wheels) | [PACKAGING.md](PACKAGING.md) |
| Release process | [RELEASE_PROCESS.md](RELEASE_PROCESS.md) |
| Writing documentation | [DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) |
| Architecture decisions (ADR log) | [DECISIONS.md](DECISIONS.md) |
| Generated API reference | [../API_REFERENCE.md](../API_REFERENCE.md) |
| Generated file-format reference | [../FILE_FORMATS.md](../FILE_FORMATS.md) |
| Tests and validation | [../VALIDATION.md](../VALIDATION.md), [../tester/TESTING_GUIDE.md](../tester/TESTING_GUIDE.md) |

## Five-minute orientation
```
astrax/   physics + tools, pure Python/NumPy, NO Qt   <- change physics here, add tests in tests/
ui/       PyQt6 interface, NO physics                 <- change visuals/panels here
tools/    developer scripts (docs generation, branding, benchmark, diagnostics)
tests/    unittest suite (engine + repository health)
docs/     documentation (some files are generated: do not hand-edit)
```
Run: `python main.py` · Test: `python -m unittest discover -s tests -v` · Lint: `ruff check .` · Docs: `python tools/gen_docs.py && python tools/check_docs_links.py`.

## Good first contributions
Add an example rocket · add a challenge · improve a tooltip/doc · add a manual test case (`tools/gen_test_cases.py`) · add a unit test for an untested function · fix a TROUBLESHOOTING gap · add a compatibility-matrix row.
