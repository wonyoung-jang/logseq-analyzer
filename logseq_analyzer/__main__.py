"""Main entry point for the Logseq Analyzer application."""

import sys

from logseq_analyzer.app import run_app
from logseq_analyzer.gui.main_window import LogseqAnalyzerGUI

from PySide6.QtWidgets import QApplication


def main():
    """
    Main function to run the Logseq Analyzer application.
    """
    if "--gui" in sys.argv:
        app = QApplication()
        gui = LogseqAnalyzerGUI()
        gui.show()
        sys.exit(app.exec())
    else:
        run_app()


if __name__ == "__main__":
    main()
