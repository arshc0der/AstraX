"""System report for bug reports:   python main.py --diagnostics   (also writes diagnostics.txt)"""
import importlib.metadata as md, os, platform, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def report() -> str:
    sys.path.insert(0, ROOT)
    L = []
    try:
        import astrax; L.append(f"AstraX            : {astrax.__version__}")
    except Exception as e: L.append(f"AstraX            : import failed ({e})")
    L += [f"Python            : {sys.version.split()[0]} ({platform.python_implementation()}) {platform.architecture()[0]}", f"Platform          : {platform.platform()}", f"Machine           : {platform.machine()} | {platform.processor() or 'n/a'}",
          f"Executable        : {sys.executable}", f"Working directory : {os.getcwd()}"]
    for pkg in ("PyQt6", "PyQt6-Qt6", "pyqtgraph", "numpy", "PyOpenGL", "Pillow", "matplotlib"):
        try: L.append(f"{pkg:<18}: {md.version(pkg)}")
        except md.PackageNotFoundError: L.append(f"{pkg:<18}: not installed")
    try:
        from ui import gpu
        gp = gpu.detect_gpus(); L.append("GPUs detected     : " + (", ".join(f"{g['name']} ({g['kind']})" for g in gp) if gp else "none found")); L.append(f"Auto would choose : {gpu.choose_backend('auto', gp)} rendering")
        if sys.platform == "win32": L.append(f"Windows GPU pref  : {gpu.windows_gpu_preference(sys.executable)}")
    except Exception as e: L.append(f"GPU detection     : failed ({e})")
    try:
        from PyQt6.QtCore import QSettings
        st = QSettings("AstraX", "AstraX2"); L.append("Settings          : " + ", ".join(f"{k}={st.value(k)}" for k in ("theme", "gfx_mode", "gfx_prefer_discrete", "gfx_quality", "fps_cap", "show_splash") if st.contains(k)) or "defaults")
    except Exception as e: L.append(f"Settings          : unavailable ({e})")
    for k in ("QT_OPENGL", "QT_QPA_PLATFORM", "QT_SCALE_FACTOR", "DRI_PRIME", "DISPLAY", "WAYLAND_DISPLAY"):
        if os.environ.get(k): L.append(f"env {k:<14}: {os.environ[k]}")
    logs = os.path.join(ROOT, "logs"); L.append(f"Log folder        : {logs} ({len(os.listdir(logs)) if os.path.isdir(logs) else 0} files)")
    try:
        import numpy as np, time
        t = time.perf_counter(); a = np.random.rand(300, 300); (a @ a); L.append(f"NumPy 300x300 matmul: {(time.perf_counter() - t) * 1000:.1f} ms")
        from astrax.simulation import Simulation, SimConfig
        s = Simulation(config=SimConfig(dt_s=0.05)); t = time.perf_counter(); [s.step() for _ in range(2000)]; L.append(f"Physics 2000 steps : {(time.perf_counter() - t) * 1000:.0f} ms (engine self-test OK)")
    except Exception as e: L.append(f"Engine self-test  : FAILED ({type(e).__name__}: {e})")
    return "\n".join(L)


def run():
    text = report(); print(text)
    try: open(os.path.join(os.getcwd(), "diagnostics.txt"), "w", encoding="utf-8").write(text + "\n"); print("\n(written to diagnostics.txt - attach it to your bug report)")
    except Exception: pass


if __name__ == "__main__":
    run()
