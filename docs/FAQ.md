# FAQ and troubleshooting

**Is AstraX accurate enough for real mission planning?** No. It uses simplified, documented models and mean orbital elements. It is for learning, design exploration and research prototyping. See [PHYSICS](PHYSICS.md).

**`pip.exe` is blocked / "Application Control policy".** Use `python -m pip install -r requirements.txt`. If a Qt DLL is blocked, retry or ask your IT admin to allow the venv folder.

**The window is bigger than my screen.** *View ▸ Reset window layout*, restart. Panels scroll when space is tight.

**The splash is slow / I don't want it.** `python main.py --no-splash`, or Settings ▸ untick *Show animated splash*.

**The title bar is not dark.** Native title-bar colouring works on Windows 10 (1809+) and 11. On Linux/macOS the OS draws it.

**Windows file dialogs are light.** They are native OS dialogs and follow the Windows theme.

**Run is slower than the speed I picked.** Your CPU cannot keep up; the status bar shows requested vs achieved speed. AstraX never coarsens the physics to catch up. Lower the speed, use `verlet`, or `auto` dt.

**Warning "dt advances X rad of orbit per step".** The fixed timestep is too big for the orbit. Switch dt mode to **auto**.

**Survival test says LOST, but my design looks fine.** The standard ascent profile may not suit it (kick angle, throttle). Read the reason; try the *Parameter sweep*; adjust design limits; or fly it manually with your own flight plan.

**"Cannot lift off".** Sea-level thrust-to-weight is below 1 for the chosen launch body (see *Launch body* in the designer).

**My lander crashes.** Landing needs thrust > weight on that body. Check T/W for the Moon, raise thrust or reduce mass; the landing guidance ignites when the stopping deceleration reaches ~85 % of available.

**Where are my logs?** `logs/astrax_<timestamp>.log` next to `main.py` (Tools ▸ Open logs folder).

**Where are settings stored?** Qt `QSettings` (organisation "AstraX", application "AstraX2"): registry on Windows, `~/.config` on Linux.

**Can I run it without a GUI?** Yes: the engine in `astrax/` has no Qt dependency ([SCRIPTING_API](SCRIPTING_API.md)).

**How do I report a bug?** Include the full terminal text, the steps, and a screenshot.
