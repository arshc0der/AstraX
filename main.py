"""AstraX entry point:  python main.py [--no-splash] [--gpu | --cpu] [--gpu-info] [--diagnostics]"""
import os, sys, threading, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def _preload():
    """Import the heavy, GUI-free modules on a worker thread while the splash animates."""
    for m in ("numpy", "PIL.Image", "OpenGL.GL", "astrax.simulation", "astrax.rocket_mesh", "astrax.survival", "astrax.transfer", "astrax.studies", "astrax.challenges"):
        try: __import__(m)
        except Exception: pass


def main():
    if "--diagnostics" in sys.argv:                    # system report for bug reports (no window)
        from tools.diagnostics import run; run(); return
    from ui import gpu
    if "--gpu-info" in sys.argv:                       # diagnostics without opening any window
        g = gpu.detect_gpus(); print("Detected GPUs:"); [print(f"  - {x['name']} ({x['kind']})") for x in g] or print("  none"); print("Auto would choose:", gpu.choose_backend("auto", g)); return
    from PyQt6.QtCore import QSettings as _QS
    _st = _QS("AstraX", "AstraX2")
    mode = "gpu" if "--gpu" in sys.argv else "cpu" if "--cpu" in sys.argv else str(_st.value("gfx_mode", "auto"))
    gfx = gpu.configure_graphics(mode, str(_st.value("gfx_prefer_discrete", "false")).lower() == "true", str(_st.value("gfx_quality", "auto")))   # must precede QApplication
    sys.setswitchinterval(0.002)                        # give the GUI thread the GIL more often while the physics thread runs
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import Qt, QSettings
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv); app.setApplicationName("AstraX"); app.setOrganizationName("AstraX")
    icon = os.path.join(BASE, "assets", "logo.ico" if sys.platform == "win32" else "logo.png")
    if os.path.exists(icon): app.setWindowIcon(QIcon(icon))
    from ui.theme import apply_app_theme, THEMES, build_style
    st = QSettings("AstraX", "AstraX2"); theme = str(st.value("theme", "Mission control (dark)"))
    pal = apply_app_theme(app, theme); app.setStyleSheet(build_style(theme, int(st.value("font_pt", 10))))
    from ui.winframe import FrameFilter
    frames = FrameFilter(pal, app); app.installEventFilter(frames)           # dark/themed native title bars on Windows
    show_splash = "--no-splash" not in sys.argv and str(st.value("show_splash", "true")).lower() == "true"
    splash = None
    if show_splash:
        from ui.splash import AnimatedSplash
        splash = AnimatedSplash(os.path.join(BASE, "assets", "splash"), bg=pal["BG"], border=pal["BORDER"]); splash.start()
    th = threading.Thread(target=_preload, daemon=True); th.start()
    while th.is_alive(): app.processEvents(); time.sleep(0.01)             # keep the animation running while modules load
    from ui.main_window import MainWindow
    app.processEvents(); w = MainWindow(); w.frame_filter = frames; w.gfx = gfx
    if splash is not None: splash.finish(w)
    else: w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
