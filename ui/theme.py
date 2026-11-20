"""Dark 'mission control' theme + procedurally drawn vector icons (no image files needed)."""
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF

THEMES = {
    "Mission control (dark)": dict(BG="#0b0f14", PANEL="#10161d", PANEL2="#151c25", BORDER="#243040", TEXT="#d6dee8", MUTED="#7e8b9a", ACCENT="#2aa9ff", ACCENT2="#ff7a2a", OK="#34d399", WARN="#fbbf24", ERR="#f87171"),
    "Midnight blue": dict(BG="#080d1f", PANEL="#0d1530", PANEL2="#121c3d", BORDER="#27366b", TEXT="#dbe4ff", MUTED="#8190c0", ACCENT="#6ea8ff", ACCENT2="#ffb454", OK="#4ade80", WARN="#facc15", ERR="#fb7185"),
    "High contrast": dict(BG="#000000", PANEL="#0a0a0a", PANEL2="#161616", BORDER="#8a8a8a", TEXT="#ffffff", MUTED="#c0c0c0", ACCENT="#00e5ff", ACCENT2="#ffab00", OK="#00ff7f", WARN="#ffd600", ERR="#ff5252"),
    "Light": dict(BG="#eef1f5", PANEL="#ffffff", PANEL2="#e3e8ef", BORDER="#b8c2d0", TEXT="#1b2430", MUTED="#5d6b7c", ACCENT="#0b6fd1", ACCENT2="#d9480f", OK="#0a8f5f", WARN="#b7791f", ERR="#c92a2a"),
}
_KEYS = ("BG", "PANEL", "PANEL2", "BORDER", "TEXT", "MUTED", "ACCENT", "ACCENT2", "OK", "WARN", "ERR")
BG, PANEL, PANEL2, BORDER, TEXT, MUTED, ACCENT, ACCENT2, OK, WARN, ERR = [THEMES["Mission control (dark)"][k] for k in _KEYS]


def build_style(theme="Mission control (dark)", pt=10):
    """Qt stylesheet for the chosen colour theme and base font size (points)."""
    global BG, PANEL, PANEL2, BORDER, TEXT, MUTED, ACCENT, ACCENT2, OK, WARN, ERR
    BG, PANEL, PANEL2, BORDER, TEXT, MUTED, ACCENT, ACCENT2, OK, WARN, ERR = [THEMES.get(theme, THEMES["Mission control (dark)"])[k] for k in _KEYS]
    return f"""
    * {{ font-family: 'Inter','Segoe UI','Helvetica Neue',Arial,sans-serif; font-size: {pt}pt; color: {TEXT}; }}
    QMainWindow, QDialog {{ background: {BG}; }}
    QDockWidget {{ titlebar-close-icon: none; font-weight: 600; }}
    QDockWidget::title {{ background: {PANEL2}; padding: 6px 10px; border-bottom: 1px solid {BORDER}; letter-spacing: 1px; text-transform: uppercase; }}
    QWidget#panel, QDockWidget > QWidget {{ background: {PANEL}; }}
    QTabWidget::pane {{ border: 1px solid {BORDER}; background: {PANEL}; top: -1px; }}
    QTabBar::tab {{ background: {PANEL2}; padding: 7px 16px; border: 1px solid {BORDER}; border-bottom: none; color: {MUTED}; }}
    QTabBar::tab:selected {{ color: {TEXT}; background: {PANEL}; border-top: 2px solid {ACCENT}; }}
    QGroupBox {{ border: 1px solid {BORDER}; border-radius: 6px; margin-top: 14px; padding-top: 10px; background: {PANEL}; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; color: {ACCENT}; font-weight: 600; }}
    QPushButton {{ background: {PANEL2}; border: 1px solid {BORDER}; border-radius: 5px; padding: 6px 12px; }}
    QPushButton:hover {{ border-color: {ACCENT}; background: #1a2430; }}
    QPushButton:pressed {{ background: #0f151c; }}
    QPushButton#primary {{ background: {ACCENT}; color: #04121e; font-weight: 700; border: none; }}
    QPushButton#primary:hover {{ background: #5cc0ff; }}
    QPushButton#danger {{ background: #5b1d1d; border-color: #8a2a2a; }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit, QTextBrowser, QTableWidget, QTreeWidget, QListWidget {{
      background: #0a0e13; border: 1px solid {BORDER}; border-radius: 4px; padding: 3px 6px; selection-background-color: #1c4f75; }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QHeaderView::section {{ background: {PANEL2}; border: none; border-right: 1px solid {BORDER}; padding: 4px 8px; color: {MUTED}; }}
    QTableWidget {{ gridline-color: {BORDER}; }}
    QToolBar {{ background: {PANEL2}; border-bottom: 1px solid {BORDER}; spacing: 4px; padding: 4px; }}
    QToolButton {{ border: 1px solid transparent; border-radius: 5px; padding: 5px; }}
    QToolButton:hover {{ border-color: {ACCENT}; background: #1a2430; }}
    QToolButton:checked {{ background: #12354f; border-color: {ACCENT}; }}
    QStatusBar {{ background: {PANEL2}; border-top: 1px solid {BORDER}; color: {MUTED}; }}
    QMenuBar {{ background: {PANEL2}; }} QMenuBar::item:selected, QMenu::item:selected {{ background: #1c4f75; }}
    QMenu {{ background: {PANEL}; border: 1px solid {BORDER}; }}
    QSplitter::handle {{ background: {BORDER}; }}
    QScrollBar:vertical {{ background: {PANEL}; width: 10px; }} QScrollBar::handle:vertical {{ background: #2b384a; border-radius: 4px; min-height: 24px; }}
    QScrollBar:horizontal {{ background: {PANEL}; height: 10px; }} QScrollBar::handle:horizontal {{ background: #2b384a; border-radius: 4px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
    QToolTip {{ background: {PANEL2}; color: {TEXT}; border: 1px solid {ACCENT}; padding: 4px; }}
    QLabel#h1 {{ font-size: 13pt; font-weight: 700; color: {ACCENT}; }}
    QLabel#muted {{ color: {MUTED}; }}
    QLabel#estimate {{ color: {WARN}; font-weight: 600; }}
    QLabel#mono {{ font-family: 'JetBrains Mono','Consolas','Menlo',monospace; color: {OK}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {ACCENT}; width: 12px; margin: -5px 0; border-radius: 6px; }}
    QProgressBar {{ background: #0a0e13; border: 1px solid {BORDER}; border-radius: 4px; text-align: center; }}
    QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
    """



STYLE = build_style()


def _icon(draw, color=TEXT, size=48):
    pm = QPixmap(size, size); pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(color), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); p.setBrush(QBrush(QColor(color)))
    draw(p, size); p.end(); return QIcon(pm)


def _poly(p, pts): p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))


def make_icon(name: str, color=TEXT) -> QIcon:
    def play(p, s): _poly(p, [(s * .3, s * .2), (s * .8, s * .5), (s * .3, s * .8)])
    def pause(p, s): p.drawRect(QRectF(s * .28, s * .2, s * .15, s * .6)); p.drawRect(QRectF(s * .57, s * .2, s * .15, s * .6))
    def stop(p, s): p.drawRect(QRectF(s * .25, s * .25, s * .5, s * .5))
    def reset(p, s): p.setBrush(Qt.BrushStyle.NoBrush); p.drawArc(QRectF(s * .2, s * .2, s * .6, s * .6), 40 * 16, 290 * 16); p.setBrush(QBrush(QColor(color))); _poly(p, [(s * .62, s * .08), (s * .84, s * .3), (s * .52, s * .34)])
    def slower(p, s): _poly(p, [(s * .5, s * .25), (s * .15, s * .5), (s * .5, s * .75)]); _poly(p, [(s * .85, s * .25), (s * .5, s * .5), (s * .85, s * .75)])
    def faster(p, s): _poly(p, [(s * .15, s * .25), (s * .5, s * .5), (s * .15, s * .75)]); _poly(p, [(s * .5, s * .25), (s * .85, s * .5), (s * .5, s * .75)])
    def rocket(p, s): _poly(p, [(s * .5, s * .08), (s * .65, s * .35), (s * .65, s * .7), (s * .35, s * .7), (s * .35, s * .35)]); _poly(p, [(s * .35, s * .55), (s * .2, s * .78), (s * .35, s * .72)]); _poly(p, [(s * .65, s * .55), (s * .8, s * .78), (s * .65, s * .72)])
    def planet(p, s): p.drawEllipse(QRectF(s * .25, s * .25, s * .5, s * .5)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawEllipse(QRectF(s * .08, s * .4, s * .84, s * .2))
    def chart(p, s): p.setBrush(Qt.BrushStyle.NoBrush); p.drawPolyline(QPolygonF([QPointF(s * .1, s * .75), QPointF(s * .35, s * .45), QPointF(s * .55, s * .6), QPointF(s * .9, s * .2)]))
    def rec(p, s): p.drawEllipse(QRectF(s * .22, s * .22, s * .56, s * .56))
    def camera(p, s): p.setBrush(Qt.BrushStyle.NoBrush); p.drawRect(QRectF(s * .12, s * .28, s * .76, s * .5)); p.drawEllipse(QRectF(s * .38, s * .38, s * .24, s * .3))
    def step(p, s): _poly(p, [(s * .2, s * .2), (s * .6, s * .5), (s * .2, s * .8)]); p.drawRect(QRectF(s * .68, s * .2, s * .12, s * .6))
    def stage(p, s): p.drawRect(QRectF(s * .3, s * .15, s * .4, s * .25)); p.drawRect(QRectF(s * .3, s * .6, s * .4, s * .25))
    return _icon({"play": play, "pause": pause, "stop": stop, "reset": reset, "slower": slower, "faster": faster, "rocket": rocket,
                  "planet": planet, "chart": chart, "record": rec, "camera": camera, "step": step, "stage": stage}[name], color)
