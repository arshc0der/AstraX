"""AstraX entry point:  python main.py"""
import os, sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt


def main():
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv); app.setApplicationName("AstraX")
    base = os.path.dirname(os.path.abspath(__file__)); icon = os.path.join(base, "assets", "logo.png")
    if os.path.exists(icon): app.setWindowIcon(QIcon(icon))
    from ui.main_window import MainWindow
    w = MainWindow(); w.show(); sys.exit(app.exec())


if __name__ == "__main__":
    main()
