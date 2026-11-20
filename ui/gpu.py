"""GPU detection and graphics-backend selection (Auto / GPU / CPU).

What the GPU does in AstraX: it DRAWS the 3D scene through OpenGL. The physics (NumPy) always runs on the CPU, so a low GPU
percentage in Task Manager is normal for a small scene; lag is usually CPU/Python-bound. What this module fixes:
  * Qt falling back to *software* OpenGL (CPU rendering)            -> choose mode GPU / Auto
  * laptops with two GPUs running AstraX on the weak integrated one -> 'prefer discrete GPU' (Windows registry preference / Linux PRIME env)
Everything here must run BEFORE the QApplication is created (the backend cannot change afterwards): changes need a restart.
Module level imports are stdlib only so the parsing/selection logic is unit-testable without Qt.
"""
from __future__ import annotations
import os, re, subprocess, sys

SOFTWARE_MARKERS = ("llvmpipe", "softpipe", "lavapipe", "swiftshader", "microsoft basic render", "gdi generic", "mesa offscreen", "software rasterizer", "software renderer")
DISCRETE_RE = re.compile(r"nvidia|geforce|quadro|\brtx\b|\bgtx\b|titan|radeon (rx|pro|vii|r[579])|intel\(r\) arc|arc a\d|firepro", re.I)
INTEGRATED_RE = re.compile(r"intel|uhd|iris|radeon\(tm\) graphics|radeon graphics|vega \d|apple m\d|adreno|mali", re.I)
MODES = ("auto", "gpu", "cpu")


def is_software_renderer(name: str) -> bool:
    n = (name or "").lower(); return any(m in n for m in SOFTWARE_MARKERS)


def classify(name: str) -> str:
    """'software' | 'discrete' | 'integrated' | 'unknown' from a GPU/renderer name."""
    if is_software_renderer(name): return "software"
    if DISCRETE_RE.search(name or ""): return "discrete"
    if INTEGRATED_RE.search(name or ""): return "integrated"
    return "unknown"


def parse_lspci(text: str) -> list:
    out = []
    for line in text.splitlines():
        if re.search(r"VGA compatible|3D controller|Display controller", line):
            name = line.split(": ", 1)[-1].strip(); out.append(dict(name=name, kind=classify(name)))
    return out


def _windows_gpus() -> list:
    out = []
    try:
        import winreg
        base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base) as k:
            for i in range(32):
                try: sub = winreg.EnumKey(k, i)
                except OSError: break
                if not sub.isdigit(): continue
                try:
                    with winreg.OpenKey(k, sub) as sk:
                        name = winreg.QueryValueEx(sk, "DriverDesc")[0]
                        try: mem = winreg.QueryValueEx(sk, "HardwareInformation.qwMemorySize")[0]
                        except OSError: mem = 0
                        out.append(dict(name=str(name), kind=classify(str(name)), vram_gb=round(int(mem) / 2 ** 30, 1) if mem else None))
                except OSError: continue
    except Exception:
        pass
    return out


def detect_gpus() -> list:
    """List of installed GPUs: dicts with name, kind (discrete/integrated/software/unknown). Never raises."""
    try:
        if sys.platform == "win32": return _windows_gpus()
        if sys.platform == "darwin":
            r = subprocess.run(["system_profiler", "SPDisplaysDataType"], capture_output=True, text=True, timeout=8)
            names = re.findall(r"Chipset Model:\s*(.+)", r.stdout); return [dict(name=n.strip(), kind=classify(n)) for n in names]
        r = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5); return parse_lspci(r.stdout)
    except Exception:
        return []


def choose_backend(mode: str, gpus: list) -> str:
    """Resolve 'auto' to 'gpu' or 'cpu'. Auto uses the GPU unless the only adapter found is a software one."""
    if mode in ("gpu", "cpu"): return mode
    hw = [g for g in gpus if g["kind"] in ("discrete", "integrated", "unknown")]
    return "gpu" if hw or not gpus else "cpu"


def set_windows_gpu_preference(exe_path: str, high_performance: bool = True) -> bool:
    """Windows 10 1803+: tell Windows to run this python.exe on the high-performance GPU (same as Settings > Graphics). Effective after restart."""
    if sys.platform != "win32": return False
    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\DirectX\UserGpuPreferences") as k:
            winreg.SetValueEx(k, exe_path, 0, winreg.REG_SZ, "GpuPreference=2;" if high_performance else "GpuPreference=0;")
        return True
    except Exception:
        return False


def windows_gpu_preference(exe_path: str):
    if sys.platform != "win32": return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\DirectX\UserGpuPreferences") as k: return winreg.QueryValueEx(k, exe_path)[0]
    except Exception:
        return None


def configure_graphics(mode="auto", prefer_discrete=False, quality="auto") -> dict:
    """Select the OpenGL backend. Call BEFORE creating QApplication. Returns a dict describing the choice."""
    gpus = detect_gpus(); backend = choose_backend(mode, gpus)
    if prefer_discrete and sys.platform.startswith("linux"):
        os.environ.setdefault("DRI_PRIME", "1"); os.environ.setdefault("__NV_PRIME_RENDER_OFFLOAD", "1"); os.environ.setdefault("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
    if prefer_discrete and sys.platform == "win32": set_windows_gpu_preference(sys.executable, True)
    os.environ["QT_OPENGL"] = "software" if backend == "cpu" else "desktop"
    try:
        from PyQt6.QtCore import QCoreApplication, Qt
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL if backend == "cpu" else Qt.ApplicationAttribute.AA_UseDesktopOpenGL, True)
        from PyQt6.QtGui import QSurfaceFormat
        fmt = QSurfaceFormat(); fmt.setDepthBufferSize(24); fmt.setSwapInterval(1)
        fmt.setSamples(0 if (quality == "performance" or backend == "cpu") else 4); QSurfaceFormat.setDefaultFormat(fmt)
    except Exception:
        pass
    return dict(requested=mode, backend=backend, prefer_discrete=prefer_discrete, quality=quality, gpus=gpus)


def restart_app():
    """Relaunch the application with the same arguments."""
    try: subprocess.Popen([sys.executable] + sys.argv)
    finally: os._exit(0)
