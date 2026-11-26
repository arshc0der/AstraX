# Tester hub

Welcome, tester! You do not need to write code. Your job: **use AstraX like a user would, try to break it, and report clearly.** Every report makes the project better for the many people who use it.

## Start here
| I want to... | Read |
|---|---|
| run a quick sanity check (15 min) | [SMOKE_TEST.md](SMOKE_TEST.md) |
| run the full manual suite | [MANUAL_TEST_CASES.md](MANUAL_TEST_CASES.md) (+ [CSV](test_cases.csv)) |
| re-test before a release | [REGRESSION_CHECKLIST.md](REGRESSION_CHECKLIST.md) |
| explore freely (session-based) | [EXPLORATORY_CHARTERS.md](EXPLORATORY_CHARTERS.md) |
| report a bug well | [BUG_REPORTING.md](BUG_REPORTING.md) |
| test speed and smoothness | [PERFORMANCE_TESTING.md](PERFORMANCE_TESTING.md) |
| test on my OS/GPU | [COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md) |
| understand the strategy | [TESTING_GUIDE.md](TESTING_GUIDE.md), [TEST_PLAN.md](TEST_PLAN.md) |
| check a release | [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) |
| know current limitations | [KNOWN_ISSUES.md](KNOWN_ISSUES.md) |
| look up expected values | [TEST_DATA.md](TEST_DATA.md) |

## The 5-minute tester workflow
1. `python main.py --diagnostics` → keep the output (it goes in every report).
2. Run the [smoke test](SMOKE_TEST.md).
3. Pick an area (or a charter) and spend 30–60 minutes there.
4. For each problem: reproduce it twice, then use the *Bug report* issue form.
5. Post a summary using the *Test report* issue form.

## What we value
- **Clear steps** that someone else can follow.
- **Evidence**: screenshot, log file, `diagnostics.txt`, the scenario/rocket JSON that triggers it.
- **Environment diversity**: Windows/Linux/macOS, integrated vs discrete GPU, high-DPI, slow laptops.
- **Scientific sanity**: if a number looks physically wrong, say so and say why (compare with [TEST_DATA.md](TEST_DATA.md) or a textbook).

## Tester etiquette
Be specific and kind; one problem per issue; do not report the same thing twice (search first); mark duplicates; confirm fixes when asked.
