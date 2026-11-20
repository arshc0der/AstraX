"""Educational challenges: run headless for a pass/fail verdict, or load the scenario in 3D."""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QTextBrowser
from astrax.challenges import CHALLENGES
from ui.worker_util import FuncWorker


def _run(name, progress=None): return CHALLENGES[name][0]()


class ChallengesPanel(QWidget):
    load_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__(); v = QVBoxLayout(self); v.addWidget(QLabel("Challenges", objectName="h1")); self.list = QListWidget(); self.list.setMaximumHeight(120)
        for n, (fn, d) in CHALLENGES.items(): self.list.addItem(n)
        self.list.setCurrentRow(0); self.list.currentTextChanged.connect(self._sel); v.addWidget(self.list); self.desc = QLabel(""); self.desc.setWordWrap(True); v.addWidget(self.desc)
        row = QHBoxLayout(); self.run = QPushButton("Run (headless verdict)"); self.run.setObjectName("primary"); self.run.clicked.connect(self._start); row.addWidget(self.run)
        b = QPushButton("Load in 3D"); b.clicked.connect(lambda: self.list.currentItem() and self.load_requested.emit(self.list.currentItem().text())); row.addWidget(b); v.addLayout(row)
        self.out = QTextBrowser(); v.addWidget(self.out); self.log = {}; self._sel("First orbit")

    def _sel(self, name):
        if name in CHALLENGES: self.desc.setText(CHALLENGES[name][1])

    def _start(self):
        it = self.list.currentItem()
        if not it: return
        self.run.setEnabled(False); self.out.setHtml("Running..."); self.w = FuncWorker(_run, it.text()); self.w.done.connect(self._done); self.w.failed.connect(lambda m: (self.out.setHtml(m), self.run.setEnabled(True))); self.w.start()

    def _done(self, r):
        self.run.setEnabled(True); self.log[r.name] = r.passed
        self.out.setHtml(f"<h2 style='color:{'#34d399' if r.passed else '#f87171'}'>{'PASSED' if r.passed else 'NOT YET'} - {r.name}</h2><p>{r.message}</p><hr>" + "<br>".join(f"{'&#10003;' if v else '&#10007;'} {k}" for k, v in self.log.items()))
