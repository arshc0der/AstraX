# Exploratory testing charters

Exploratory testing = learn, design tests and execute them at the same time. Each **session is 45–60 minutes**, time-boxed, with a **mission**. Take notes as you go and file what you find.

**Charter format:** *Explore [area] with [resources/data] to discover [risks].*

| # | Charter | Ideas to try |
|---|---|---|
| 1 | Explore **rocket design extremes** with absurd values to discover crashes and bad validation | 0 engines, 1000 engines, huge/tiny diameters, negative-looking values, 50 stages, very long names, dry mass larger than the rocket |
| 2 | Explore **survival-test edge cases** with unusual designs to discover wrong verdicts | boosters only, no payload, 10 t payload, sounding rocket, SSTO, wall 0.1 mm / 200 mm, FoS 1.0 / 3.0 |
| 3 | Explore **time controls** while switching things mid-run to discover races and freezes | change speed/integrator/dt mid-flight, reset during staging, pause/step spam, custom 1e6x |
| 4 | Explore **cameras and layers** during dramatic events to discover rendering glitches | launch camera through staging, breakup, abort; first-person; extreme zoom; all layers on |
| 5 | Explore **flight plans** by writing odd phases to discover guidance bugs | empty plan, phases with no end, contradictory end conditions, coast forever, prograde at zero speed |
| 6 | Explore **emergencies** in every flight phase to discover state-machine errors | abort on the pad, abort in orbit, abort twice, fault + clear + abort, cutoff then stage |
| 7 | Explore **planet editing** with wild values to discover instability | Earth mass ×1000, Sun mass ×0.01, radius 1 km, Jupiter at 1 AU, reset all |
| 8 | Explore **launch-window planner** with unusual planet pairs/ranges to discover solver failures | Mercury↔Neptune, tiny/huge spans, flight-time min > max, 10 s grid |
| 9 | Explore **files** by corrupting/editing JSON to discover loader weaknesses | truncated JSON, wrong types, extra fields, huge numbers, other-format files, read-only folders |
| 10 | Explore **graphics settings** across GPU/CPU modes to discover rendering problems | switch modes, quality levels, FPS caps, multiple windows, resize, multi-monitor, high DPI |
| 11 | Explore **long-running stability** to discover leaks and slowdowns | 30–60 min at 100–1000x, multiple extra windows, repeated resets, recording |
| 12 | Explore **studies** with cancel/close mid-run to discover thread issues | close dialog during survival test, start two studies, switch tabs while running |
| 13 | Explore **usability as a newcomer** with only the Quick start to discover confusing UX | note every moment you hesitate; time to first successful launch |
| 14 | Explore **physics plausibility** to discover model errors | compare orbital periods, g-loads, Δv with textbook values; check units everywhere |
| 15 | Explore **accessibility** to discover barriers | keyboard-only operation, high-contrast theme, 16 pt font, 200 % scaling |

## Session note template
```
Charter: #__  Tester: ____  Date: ____  Duration: __ min  Build/Env: ____
Mission/approach:
Notes (timestamped):
Bugs found (issue links):
Questions / ideas:
Coverage (areas touched):  Confidence (low/med/high):
```
Heuristics to apply: **boundaries**, **empty/null**, **rapid repetition**, **interruption**, **different order**, **big/small numbers**, **units**, **undo/reset**, **parallel actions**, **environment change**.
