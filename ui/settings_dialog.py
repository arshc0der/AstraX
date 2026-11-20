"""User customisation: theme, font size, graphics (GPU/CPU), performance, viewport options. Values persist via QSettings."""
import sys
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QVBoxLayout, QLabel, QGroupBox, QMessageBox
from ui.theme import THEMES
from ui import gpu

MODE_LABELS = {"auto": "Auto (detect GPU)", "gpu": "GPU (hardware OpenGL)", "cpu": "CPU (software OpenGL)"}
QUALITY_LABELS = {"auto": "Auto", "quality": "Quality (antialiasing, detailed spheres)", "performance": "Performance (lighter drawing)"}


class SettingsDialog(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, current: dict, parent=None, gfx: dict | None = None):
        super().__init__(parent); self.setWindowTitle("Settings & customisation"); self.gfx = gfx or {}; v = QVBoxLayout(self); f = QFormLayout(); v.addLayout(f)
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(current["theme"]); f.addRow("Colour theme", self.theme)
        self.font = QSpinBox(); self.font.setRange(8, 16); self.font.setValue(current["font_pt"]); self.font.setSuffix(" pt"); f.addRow("Interface font size", self.font)
        self.trail = QSpinBox(); self.trail.setRange(100, 50000); self.trail.setSingleStep(500); self.trail.setValue(current["trail_len"]); f.addRow("Trajectory trail length (points)", self.trail)
        self.scale = QDoubleSpinBox(); self.scale.setRange(0.1, 1000); self.scale.setValue(current["body_scale"]); f.addRow("Planet size exaggeration", self.scale)
        self.splash = QCheckBox("Show animated splash screen at startup"); self.splash.setChecked(current.get("show_splash", True)); f.addRow(self.splash)
        self.plume = QCheckBox("Show engine exhaust plume"); self.plume.setChecked(current["plume"]); f.addRow(self.plume)
        self.rec = QDoubleSpinBox(); self.rec.setRange(0.05, 3600); self.rec.setValue(current["record_interval_s"]); self.rec.setSuffix(" s"); f.addRow("Telemetry sample interval", self.rec)
        # ---- graphics
        g = QGroupBox("Graphics & performance"); gf = QFormLayout(g); v.addWidget(g)
        self.mode = QComboBox(); [self.mode.addItem(lbl, k) for k, lbl in MODE_LABELS.items()]; self.mode.setCurrentIndex(list(MODE_LABELS).index(current.get("gfx_mode", "auto"))); self.mode.setToolTip("GPU: hardware OpenGL. CPU: software OpenGL (slow, but works everywhere). Needs a restart."); gf.addRow("Rendering", self.mode)
        self.disc = QCheckBox("Prefer the high-performance (discrete) GPU"); self.disc.setChecked(current.get("gfx_prefer_discrete", False)); self.disc.setToolTip("Laptops with two GPUs: ask Windows / PRIME to run AstraX on the NVIDIA/AMD GPU. Needs a restart."); gf.addRow(self.disc)
        self.quality = QComboBox(); [self.quality.addItem(lbl, k) for k, lbl in QUALITY_LABELS.items()]; self.quality.setCurrentIndex(list(QUALITY_LABELS).index(current.get("gfx_quality", "auto"))); gf.addRow("Visual quality", self.quality)
        self.fps = QComboBox(); [self.fps.addItem(f"{n} fps", n) for n in (20, 30, 60)]; self.fps.setCurrentIndex([20, 30, 60].index(int(current.get("fps_cap", 30)))); self.fps.setToolTip("Maximum 3D/telemetry refresh rate. Lower = smoother on slow machines."); gf.addRow("Refresh rate cap", self.fps)
        gpus = self.gfx.get("gpus") or []; gl = self.gfx.get("gl") or {}
        txt = "<b>Detected GPUs:</b><br>" + ("<br>".join(f"&bull; {x['name']} <i>({x['kind']})</i>" for x in gpus) if gpus else "none detected")
        txt += f"<br><b>Rendering now with:</b> {gl.get('renderer', '(starts after the first frame)')}"
        if gl and gpu.is_software_renderer(gl.get("renderer", "")): txt += "<br><span style='color:#fbbf24'>This is CPU (software) rendering. Choose GPU mode above and restart.</span>"
        lab = QLabel(txt); lab.setWordWrap(True); gf.addRow(lab)
        if sys.platform == "win32":
            b = QPushButton("Set Windows high-performance GPU preference for Python"); b.clicked.connect(self._win_pref); gf.addRow(b)
        v.addWidget(QLabel("Panels can be dragged, tabbed, floated and resized. Use Window > New 3D view / New graph window for extra windows.", objectName="muted"))
        b = QPushButton("Apply"); b.setObjectName("primary"); b.clicked.connect(self._apply); v.addWidget(b)

    def _win_pref(self):
        ok = gpu.set_windows_gpu_preference(sys.executable, True)
        QMessageBox.information(self, "GPU preference", ("Windows will now run this Python on the high-performance GPU (same as Settings > System > Display > Graphics).\nRestart AstraX to apply." if ok else "Could not write the preference (permissions)."))

    def _apply(self):
        self.applied.emit(dict(theme=self.theme.currentText(), font_pt=self.font.value(), trail_len=self.trail.value(), body_scale=self.scale.value(), plume=self.plume.isChecked(),
                               show_splash=self.splash.isChecked(), record_interval_s=self.rec.value(), gfx_mode=self.mode.currentData(), gfx_prefer_discrete=self.disc.isChecked(),
                               gfx_quality=self.quality.currentData(), fps_cap=int(self.fps.currentData()))); self.accept()
