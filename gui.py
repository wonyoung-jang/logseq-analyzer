"""
Logseq Analyzer GUI using PySide6.
"""

import sys

from PySide6.QtWidgets import QApplication

from logseq_analyzer.gui.main_window import LogseqAnalyzerGUI


if __name__ == "__main__":
    app = QApplication()
    gui = LogseqAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
