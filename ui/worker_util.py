"""Tiny helper: run a function on a background thread with optional progress callback (keeps the GUI responsive)."""
from PyQt6.QtCore import QThread, pyqtSignal


class FuncWorker(QThread):
    progress = pyqtSignal(int, int, str)
    done = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn, *args, **kw):
        super().__init__(); self.fn, self.args, self.kw = fn, args, kw

    def run(self):
        try:
            self.done.emit(self.fn(*self.args, progress=lambda i, n, t="": self.progress.emit(int(i), int(n), str(t)), **self.kw))
        except Exception as ex:
            self.failed.emit(f"{type(ex).__name__}: {ex}")
