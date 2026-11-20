"""User customisation: theme, font size, viewport options. Values persist via QSettings."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QVBoxLayout, QLabel
from ui.theme import THEMES


class SettingsDialog(QDialog):
    applied = pyqtSignal(dict)

    def __init__(self, current: dict, parent=None):
        super().__init__(parent); self.setWindowTitle("Settings & customisation"); v = QVBoxLayout(self); f = QFormLayout(); v.addLayout(f)
        self.theme = QComboBox(); self.theme.addItems(THEMES.keys()); self.theme.setCurrentText(current["theme"]); f.addRow("Colour theme", self.theme)
        self.font = QSpinBox(); self.font.setRange(8, 16); self.font.setValue(current["font_pt"]); self.font.setSuffix(" pt"); f.addRow("Interface font size", self.font)
        self.trail = QSpinBox(); self.trail.setRange(100, 50000); self.trail.setSingleStep(500); self.trail.setValue(current["trail_len"]); f.addRow("Trajectory trail length (points)", self.trail)
        self.scale = QDoubleSpinBox(); self.scale.setRange(0.1, 1000); self.scale.setValue(current["body_scale"]); f.addRow("Planet size exaggeration", self.scale)
        self.plume = QCheckBox("Show engine exhaust plume"); self.plume.setChecked(current["plume"]); f.addRow(self.plume)
        self.rec = QDoubleSpinBox(); self.rec.setRange(0.05, 3600); self.rec.setValue(current["record_interval_s"]); self.rec.setSuffix(" s"); f.addRow("Telemetry sample interval", self.rec)
        v.addWidget(QLabel("Panels can be dragged, tabbed, floated and resized. Use View > New 3D view / New graph window for extra windows.", objectName="muted"))
        b = QPushButton("Apply"); b.setObjectName("primary"); b.clicked.connect(self._apply); v.addWidget(b)

    def _apply(self):
        self.applied.emit(dict(theme=self.theme.currentText(), font_pt=self.font.value(), trail_len=self.trail.value(), body_scale=self.scale.value(), plume=self.plume.isChecked(), record_interval_s=self.rec.value())); self.accept()
