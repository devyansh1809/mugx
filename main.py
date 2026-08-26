"""
main.py -- SubliStudio v2 entry point.

Run with:
    python main.py
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow

APP_DATA_DIR = Path.home() / ".subli_studio"
LOG_DIR = APP_DATA_DIR / "logs"


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "subli_studio.log"),
            logging.StreamHandler(),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("SubliStudio.Main")
    logger.info("Starting SubliStudio v2...")

    app = QApplication(sys.argv)
    app.setApplicationName("SubliStudio")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
