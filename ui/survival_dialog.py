"""Design survival test: runs in a background thread, then shows verdict, margins and failure timeline."""
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QProgressBar, QTextBrowser, QCheckBox
from astrax.survival import run_survival_test


class SurvivalWorker(QThread):
    progress = pyqtSignal(int, int, str)
    done = pyqtSignal(object)

    def __init__(self, rocket, system, protect):
        super().__init__(); self.rocket, self.system, self.protect = rocket, system, protect

    def run(self):
        try: self.done.emit(run_survival_test(self.rocket, self.system, protect=self.protect, progress=lambda i, n, t: self.progress.emit(i, n, t)))
        except Exception as ex: self.done.emit(ex)


class SurvivalDialog(QDialog):
    watch_requested = pyqtSignal(object, float)        # rocket, kick angle

    def __init__(self, rocket, system, parent=None):
        super().__init__(parent); self.setWindowTitle("Design survival test"); self.resize(760, 640); self.rocket, self.system = rocket, system; self.outcome = None
        v = QVBoxLayout(self); self.title = QLabel("Will this rocket survive launch and reach a stable orbit?"); self.title.setObjectName("h1"); v.addWidget(self.title)
        self.protect = QCheckBox("Autopilot load protection (throttle down for max-Q / g limits)"); self.protect.setChecked(True); v.addWidget(self.protect)
        self.bar = QProgressBar(); self.bar.setRange(0, 0); self.bar.setVisible(False); v.addWidget(self.bar)
        self.verdict = QLabel(""); self.verdict.setWordWrap(True); self.verdict.setStyleSheet("font-size: 14pt; font-weight: 700; padding: 8px;"); v.addWidget(self.verdict)
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["Quantity", "Peak", "Design limit", "Margin"]); self.table.horizontalHeader().setStretchLastSection(True); v.addWidget(self.table)
        self.text = QTextBrowser(); self.text.setMaximumHeight(170); v.addWidget(self.text)
        row = QHBoxLayout(); self.run_btn = QPushButton("Run survival test"); self.run_btn.setObjectName("primary"); self.run_btn.clicked.connect(self.start); row.addWidget(self.run_btn)
        self.watch_btn = QPushButton("Watch this launch in 3D"); self.watch_btn.setEnabled(False); self.watch_btn.clicked.connect(self._watch); row.addWidget(self.watch_btn)
        b = QPushButton("Close"); b.clicked.connect(self.close); row.addWidget(b); v.addLayout(row)

    def start(self):
        self.run_btn.setEnabled(False); self.watch_btn.setEnabled(False); self.bar.setVisible(True); self.verdict.setText("Simulating ascent...")
        self.w = SurvivalWorker(self.rocket, self.system, self.protect.isChecked()); self.w.progress.connect(lambda i, n, t: self.verdict.setText(t)); self.w.done.connect(self._done); self.w.start()

    def _done(self, r):
        self.bar.setVisible(False); self.run_btn.setEnabled(True)
        if isinstance(r, Exception): self.verdict.setText(f"Test failed to run: {r}"); return
        self.outcome = r; ok = r.survived
        self.verdict.setStyleSheet(f"font-size: 14pt; font-weight: 700; padding: 8px; color: {'#34d399' if ok else '#f87171'};"); self.verdict.setText(("PASS - " if ok else "FAIL - ") + r.headline)
        rows = []
        for name, pk, lim, unit, sc in (("Dynamic pressure (max-Q)", r.peaks["q"], r.limits["q"], "kPa", 1e3), ("Axial acceleration", r.peaks["g"], r.limits["g"], "g", 1.0),
                                          ("Nose heat flux", r.peaks["heat"], r.limits["heat"], "kW/m2", 1e3)):
            m = (lim / pk - 1) * 100 if pk > 0 else float("inf"); rows.append((name, f"{pk / sc:,.1f} {unit}", f"{lim / sc:,.1f} {unit}", f"{m:+.0f}%"))
        sr = r.peaks["stress_ratio"]; rows.append(("Structural stress (vs allowable)", f"{sr * 100:.0f}% of allowable", "100%", f"{(1 / sr - 1) * 100:+.0f}%" if sr > 0 else "inf"))
        rows.append(("Peak Mach number", f"{r.peaks['mach']:.1f}", "-", "-")); rows.append(("Orbit reached", f"{r.orbit['peri_km']:.0f} x {r.orbit['apo_km']:.0f} km, e = {r.orbit['ecc']:.3f}", "-", "-"))
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                it = QTableWidgetItem(val)
                if j == 3 and val.startswith("-") and val != "-": it.setForeground(Qt.GlobalColor.red)
                self.table.setItem(i, j, it)
        self.table.resizeColumnToContents(0)
        html = "<b>Trials (pitch-kick angle):</b><br>" + "<br>".join(f"{k:g} deg: {v} - {h}" for k, v, h in r.trials) + "<br><br><b>Event timeline:</b><br>" + "<br>".join(f"T+{t:,.0f}s {m}" for t, m in r.events[:14])
        html += "<br><br><i>" + " ".join(r.notes) + "</i>"; self.text.setHtml(html); self.watch_btn.setEnabled(True)

    def _watch(self):
        if self.outcome: self.watch_requested.emit(self.rocket, self.outcome.kick_deg); self.close()
