"""Make the native window frame (title bar + border) match the theme. Windows 10/11 only (DWM); a no-op elsewhere.

DWMWA_USE_IMMERSIVE_DARK_MODE (20, or 19 on early Win10) gives a dark title bar; DWMWA_BORDER_COLOR (34), DWMWA_CAPTION_COLOR (35)
and DWMWA_TEXT_COLOR (36) set exact colours on Windows 11 (build 22000+). Older systems just get the dark/light title bar.
"""
import sys
from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QWidget, QApplication


def _rgb(hexcol: str):
    h = hexcol.lstrip("#"); return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _colorref(hexcol: str) -> int:
    r, g, b = _rgb(hexcol); return r | (g << 8) | (b << 16)


def is_dark(hexcol: str) -> bool:
    r, g, b = _rgb(hexcol); return (0.299 * r + 0.587 * g + 0.114 * b) < 128


def apply_native_frame(widget: QWidget, bg: str, border: str, text: str) -> bool:
    """Colour the title bar of a top-level widget. Returns True if the call was attempted."""
    if sys.platform != "win32" or not widget.isWindow(): return False
    try:
        import ctypes
        from ctypes import wintypes
        hwnd = wintypes.HWND(int(widget.winId())); dwm = ctypes.windll.dwmapi

        def put(attr, val):
            v = ctypes.c_int(val); return dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
        dark = 1 if is_dark(bg) else 0
        put(20, dark); put(19, dark)
        put(35, _colorref(bg)); put(34, _colorref(border)); put(36, _colorref(text))
        return True
    except Exception:
        return False


class FrameFilter(QObject):
    """Application-wide event filter: every top-level window (dialogs, floating docks, ...) gets the themed frame when it is shown."""

    def __init__(self, colors: dict, parent=None):
        super().__init__(parent); self.colors = colors

    def set_colors(self, colors: dict):
        self.colors = colors
        for w in QApplication.topLevelWidgets():
            if w.isVisible(): apply_native_frame(w, self.colors["BG"], self.colors["BORDER"], self.colors["TEXT"])

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.Show and isinstance(obj, QWidget) and obj.isWindow():
            apply_native_frame(obj, self.colors["BG"], self.colors["BORDER"], self.colors["TEXT"])
        return False
