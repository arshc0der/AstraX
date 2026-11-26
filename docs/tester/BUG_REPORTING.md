# How to report a bug

A great bug report lets a developer reproduce the problem in minutes.

## Before reporting
1. Update to the latest release/`main`.
2. Search [existing issues](https://github.com/arshc0der/AstraX/issues) and [TROUBLESHOOTING](../TROUBLESHOOTING.md).
3. Reproduce it **twice**, ideally from a fresh start (`R` reset, or restart).

## Collect evidence
| Item | How |
|---|---|
| System report | `python main.py --diagnostics` → `diagnostics.txt` |
| Traceback | copy the full terminal text (not a screenshot of part of it) |
| Log | newest file in `logs/` (Tools ▸ Open logs folder) |
| Screenshot / recording | `Win+Shift+S`, or the app's Record button (GIF) |
| Input files | the rocket/scenario/session JSON that triggers it |
| Graphics info | status bar line `GPU: ...` / `CPU rendering: ...` |

## Write it
Use the **Bug report** form. Fields that matter most:
- **Title:** area + symptom + condition. ✅ *"Survival dialog: results table empty after running a booster rocket"* ❌ *"doesn't work"*.
- **Steps:** numbered, exact values typed/clicked, starting from app start.
- **Expected vs actual**, and a reference if it is a physics issue (equation, textbook, number).
- **Impact:** crash / unusable / wrong result / glitch / lag.
- **Frequency:** always, sometimes (how often), once.

### Template
```
Version: 4.0.0     OS: Windows 11 23H2     Python: 3.12.4     GPU: RTX 3050 + Intel UHD
Area: Survival test

Steps:
1. Designer > Example rockets > "Heavy lifter with side boosters" > Load
2. Will it survive? > Run
Expected: a verdict and margin table
Actual: dialog shows "Test failed to run: KeyError 'q'"
Frequency: always
Attachments: diagnostics.txt, log, screenshot, heavy.rocket.json
```

## Severity guide (you suggest, maintainers decide)
S1 crash/data loss · S2 feature unusable or wrong physics · S3 workaround exists · S4 cosmetic. See [TEST_PLAN](TEST_PLAN.md).

## Physics-looks-wrong reports
Say which quantity, the value you got, the value you expected and **why** (formula/source/units). Remember AstraX is a simplified model: check [PHYSICS](../PHYSICS.md) for known limitations first - then it may be a documented limit rather than a bug (still useful feedback!).

## Security issues
Do **not** use public issues: see [SECURITY.md](../../SECURITY.md).

## After reporting
Answer questions promptly; verify the fix when asked (re-run your steps on the fixed build and comment *verified*).
