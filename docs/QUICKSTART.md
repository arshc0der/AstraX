# Quick start (5 minutes)

## 1. Install
```bash
python -m venv venv
venv\Scripts\activate                 # Linux/macOS: source venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```
Python 3.10+ is required. On locked-down Windows PCs always use `python -m pip` (not `pip.exe`).
Add `--no-splash` to skip the animated intro. Graphics options: `python main.py --gpu-info` (list GPUs), `--gpu` (force hardware OpenGL), `--cpu` (force software). If it lags, see [GRAPHICS_AND_PERFORMANCE](GRAPHICS_AND_PERFORMANCE.md).

## 2. First launch
1. Right panel ▸ **Mission control** ▸ preset **Earth launch to LEO** ▸ *Load scenario preset*.
2. Toolbar camera ▸ **Launch camera**. Press **Space**.
3. Watch liftoff, the plume, staging, and orbit insertion. Banners announce events.
4. Bottom panel ▸ **Telemetry ▸ Graphs** (altitude, speed, Mach, heating...). Right panel ▸ **Orbit analysis** shows how each burn changed the orbit.

## 3. First design
1. **Rocket designer** tab ▸ *Example rockets* ▸ pick one ▸ **Load**. Edit masses, engines, wall thickness.
2. Press **Will it survive? Run survival test...** ▸ **Run**. Read the verdict and margins.
3. **Watch this launch in 3D**.

## 4. First deep-space trip
Right panel ▸ **Launch windows** ▸ *Compute launch windows* (Earth → Mars) ▸ **Fly best transfer in 3D**.

## 5. Where next
[TUTORIALS](TUTORIALS.md) for guided exercises, [USER_GUIDE](USER_GUIDE.md) for everything.
