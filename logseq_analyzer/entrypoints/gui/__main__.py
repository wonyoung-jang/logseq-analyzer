"""Main entry point for the Logseq Analyzer GUI."""

from PySide6.QtWidgets import QApplication

from logseq_analyzer.entrypoints.gui.mainwindow import LogseqAnalyzerGUI


def main() -> None:
    """Run the Logseq Analyzer application."""
    app = QApplication()
    gui = LogseqAnalyzerGUI()
    gui.show()
    app.exec()


if __name__ == "__main__":
    main()
