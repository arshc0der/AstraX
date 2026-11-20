# Graphics (GPU / CPU) and performance

## What uses the GPU - and what does not
| Part | Runs on |
|---|---|
| Drawing the 3D scene (planets, rocket, plume, lines) | **GPU** via OpenGL (or the CPU if software OpenGL is selected) |
| Physics: N-body gravity, integrators, aerodynamics, guidance | **CPU** (NumPy / Python) |
| Graphs (pyqtgraph) and the UI | CPU (Qt) |

So a low GPU percentage is normal for a small scene - the GPU is barely stressed. Lag usually comes from the **CPU/Python side** or from Windows running AstraX on the wrong graphics chip. AstraX therefore does two things: it lets you choose the rendering backend and the GPU, and it reduces the CPU work behind each frame.

## Choosing GPU or CPU rendering
**Tools ▸ Settings ▸ Graphics & performance**

| Option | Meaning |
|---|---|
| **Rendering: Auto** (default) | detect installed GPUs; use hardware OpenGL if one exists, software only if the only adapter is a software one |
| **Rendering: GPU** | force hardware OpenGL (`AA_UseDesktopOpenGL`) |
| **Rendering: CPU** | force software OpenGL (`AA_UseSoftwareOpenGL`): slow but works on any machine, useful if drivers are broken |
| **Prefer the high-performance GPU** | on laptops with two GPUs ask Windows (registry `UserGpuPreferences`) or Linux PRIME to run AstraX on the NVIDIA/AMD chip |
| **Visual quality: Auto / Quality / Performance** | Auto = Performance when rendering on the CPU, otherwise Quality |
| **Refresh rate cap: 20 / 30 / 60 fps** | upper limit for 3D and telemetry updates |
| **Set Windows high-performance GPU preference for Python** | same as *Settings ▸ System ▸ Display ▸ Graphics ▸ python.exe ▸ High performance* |

Backend and GPU preference are applied **before** the window exists, so they take effect after a restart (AstraX offers to restart for you).

### Command line
```bash
python main.py --gpu-info     # list detected GPUs and what Auto would choose (opens no window)
python main.py --gpu          # force hardware OpenGL for this run
python main.py --cpu          # force software OpenGL for this run
```

### How to see what is really rendering
- The **status bar** shows `GPU: <device>` (green) or `CPU rendering: <device>` (amber). It is read from OpenGL on the first frame (`GL_RENDERER`) and also written to the log file.
- If AstraX finds a GPU but is drawing on the CPU, it shows a one-time hint offering to open the graphics settings.
- `python main.py --gpu-info` lists the adapters Windows/Linux/macOS report.

### "GPU usage is 0% in Task Manager"
1. Task Manager ▸ **Performance ▸ GPU**: laptops list **GPU 0 = Intel/AMD integrated** and **GPU 1 = NVIDIA**. AstraX may be busy on GPU 0 while GPU 1 shows 0 %. Enable *Prefer the high-performance GPU* and restart; check GPU 1 again.
2. In Task Manager's GPU graph choose the **3D** (not *Copy*) engine and look at *Processes ▸ GPU engine* for `python.exe`.
3. A small scene legitimately uses only a few percent of a strong GPU. That is fine; it means the GPU is not the bottleneck.

## Why the app can still lag - and what was optimised
| Cause | Fix in this version |
|---|---|
| The simulation thread produced frames faster than the GUI drew them, so queued frames piled up and everything lagged more and more | **Back-pressure**: a new snapshot is sent only after the GUI finished the previous one |
| Planet orbit lines (11 × 181 points) were re-uploaded every frame | geometry uploaded **once**; each frame only a GPU translation |
| The trajectory trail converted a growing Python list to an array every frame | **ring buffer**, updated every frame (every 2nd in Performance mode) |
| Graphs re-plotted tens of thousands of points even when their tab was hidden | redraw **only the visible tab**, every ~1 s |
| Physics thread held the Python lock for too long (GIL) | shorter physics slices (12 ms), GIL switch interval 2 ms, small sleep between slices |
| Expensive 3D extras | **Performance mode**: lower sphere detail, no text labels, no atmosphere shells, no line antialiasing, no MSAA |

The status bar shows **`UI xx ms`** - the time the GUI spends handling each frame. Below ~15 ms is smooth; if it is high, lower the refresh cap or choose Performance mode.

## Practical tips
- High time acceleration (1000×) makes the **physics** work harder, not the GPU: AstraX will run slower than requested rather than skip accuracy (the status bar shows requested vs achieved speed).
- Use `verlet` or `auto` timestep for long coasts; avoid tiny fixed timesteps.
- Close extra 3D windows (each has its own scene) and floating graph windows when not needed.
- Turn off *Labels*, *Atmosphere boundary* and long trails in *View ▸ Visualisation layers* on weak machines.
- Update your graphics driver. A "Microsoft Basic Render Driver" or "llvmpipe" renderer means the real driver is not being used.

## For developers
- `ui/gpu.py`: stdlib-only detection (`detect_gpus`, `classify`, `choose_backend`, `parse_lspci`) plus `configure_graphics()` (call before `QApplication`).
- `SpaceViewport.paintGL` records `glGetString(GL_RENDERER)` once and calls `on_gl_info`.
- `SpaceViewport.set_quality("quality" | "performance")`, `SimWorker.emit_interval`, `SimWorker.ack()` for back-pressure.
- Heavy rebuilds of GL items must never happen inside `paintGL` (the main window defers them with `QTimer.singleShot(0, ...)`).
