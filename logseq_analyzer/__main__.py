"""Main entry point for the Logseq Analyzer application."""

import sys

from PySide6.QtWidgets import QApplication

from logseq_analyzer.app import run_app
from logseq_analyzer.gui.main_window import LogseqAnalyzerGUI


def main() -> None:
    """Main function to run the Logseq Analyzer application."""
    if "--cli" in sys.argv:
        run_app()
    else:
        app = QApplication()
        gui = LogseqAnalyzerGUI()
        gui.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
