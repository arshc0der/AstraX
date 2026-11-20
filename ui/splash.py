"""Animated splash screen: plays the pre-rendered frames of assets/splash (rendered from astrax-splash-animated.svg).

Frame choice is time-based, so the animation stays on schedule even when the GUI thread is briefly busy loading modules.
The window background and border use the active theme colours. After the intro (default 4 s) the last second loops until the app is ready.
"""
import glob, os, time
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import QPainter, QColor, QImage, QGuiApplication, QPen
from PyQt6.QtWidgets import QWidget, QApplication


class AnimatedSplash(QWidget):
    def __init__(self, frames_dir, bg="#0b0f14", border="#243040", fps=20, loop_seconds=1.0, min_seconds=3.8, max_width=960):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.files = sorted(glob.glob(os.path.join(frames_dir, "f*.jpg"))); self.bg, self.border = QColor(bg), QColor(border)
        self.fps, self.min_seconds = fps, min_seconds; self.loop_n = max(1, int(loop_seconds * fps)); self.t0 = time.perf_counter(); self._idx = -1; self._img = None
        scr = QGuiApplication.primaryScreen().availableGeometry(); first = QImage(self.files[0]) if self.files else QImage()
        w = min(max_width, int(scr.width() * 0.7)); h = int(w * (first.height() / first.width())) if not first.isNull() else int(w * 9 / 16)
        self.setFixedSize(w, h); self.move(scr.center().x() - w // 2, scr.center().y() - h // 2); self.setWindowTitle("AstraX")
        self.timer = QTimer(self); self.timer.timeout.connect(self._tick); self.timer.setInterval(int(1000 / fps)); self._fading = False

    def start(self):
        self.t0 = time.perf_counter(); self._tick(); self.show(); self.raise_(); self.timer.start()
        QApplication.processEvents()

    def frame_index(self):
        i = int((time.perf_counter() - self.t0) * self.fps)
        if i >= len(self.files): i = len(self.files) - self.loop_n + (i - len(self.files)) % self.loop_n   # loop the final second
        return max(0, min(i, len(self.files) - 1))

    def _tick(self):
        if not self.files: return
        i = self.frame_index()
        if i != self._idx:
            self._idx = i; img = QImage(self.files[i])
            self._img = img.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation) if not img.isNull() else None
            self.update()

    def paintEvent(self, ev):
        p = QPainter(self); p.fillRect(self.rect(), self.bg)
        if self._img is not None: p.drawImage(0, 0, self._img)
        p.setPen(QPen(self.border, 1)); p.drawRect(QRect(0, 0, self.width() - 1, self.height() - 1))

    def finish(self, window=None, fade_ms=350):
        """Wait until the intro has played, then fade out and show `window`."""
        while time.perf_counter() - self.t0 < self.min_seconds:
            QApplication.processEvents(); time.sleep(0.005)
        self.timer.stop()
        if window is not None: window.show(); window.raise_(); window.activateWindow()
        self._fading = True; self.anim = QPropertyAnimation(self, b"windowOpacity", self); self.anim.setDuration(fade_ms); self.anim.setStartValue(1.0); self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad); self.anim.finished.connect(self.close); self.anim.start()
