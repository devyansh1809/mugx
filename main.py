"""SubliStudio Phase 1 entry point."""
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.phase1_window import Phase1Window

APP_DATA_DIR = Path.home() / ".subli_studio"

def setup_logging():
    log_dir = APP_DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", handlers=[logging.FileHandler(log_dir / "subli_studio.log"), logging.StreamHandler()])

def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("SubliStudio")
    window = Phase1Window()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
