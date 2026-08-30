#!/usr/bin/env python3
"""MugX v2.2 — entry point for PyQt6 desktop application."""
import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MugX")
    app.setOrganizationName("MugX")

    # Ensure data folders exist
    data_root = Path.home() / "MugX"
    data_root.mkdir(parents=True, exist_ok=True)
    (data_root / "Customer" / "Photo").mkdir(parents=True, exist_ok=True)
    (data_root / "Templates" / "Mug").mkdir(parents=True, exist_ok=True)
    (data_root / "Templates" / "Bottle").mkdir(parents=True, exist_ok=True)
    (data_root / "Background").mkdir(parents=True, exist_ok=True)
    (data_root / "Auto" / "HD").mkdir(parents=True, exist_ok=True)
    (data_root / "Auto" / "JPG").mkdir(parents=True, exist_ok=True)

    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
