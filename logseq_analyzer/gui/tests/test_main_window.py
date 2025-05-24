"""
Test the main window of the Logseq Analyzer GUI.
"""

import pytest

from PySide6.QtWidgets import QApplication

from ..main_window import LogseqAnalyzerGUI


@pytest.fixture(scope="module")
def app():
    """Fixture for the QApplication."""
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture(scope="module")
def gui(app):
    """Fixture for the LogseqAnalyzerGUI."""
    gui = LogseqAnalyzerGUI()
    yield gui
    gui.close()


@pytest.fixture(scope="module")
def main_window(gui):
    """Fixture for the main window of the GUI."""
    gui.show()
    yield gui
    gui.close()


def test_main_window_title(main_window):
    """Test if the main window title is correct."""
    assert main_window.windowTitle() == "Logseq Analyzer"


def test_main_window_initialization(main_window):
    """Test if the main window initializes correctly."""
    assert main_window is not None
    assert main_window.isVisible() == True
    assert main_window.isEnabled() == True
    assert main_window.isActiveWindow() == True


def test_main_window_layout(main_window):
    """Test if the main window layout is set correctly."""
    layout = main_window.layout()
    assert layout is not None
    assert layout.count() > 0
    assert layout.itemAt(0) is not None
    assert layout.itemAt(0).widget() is not None


def test_main_window_controls(main_window):
    """Test if the main window controls are present."""
    assert main_window.inputs.graph_folder is not None
    assert main_window.inputs.global_config is not None
    assert main_window.inputs.report_format is not None
    assert main_window.checkboxes.move_assets is not None
    assert main_window.checkboxes.move_bak is not None
    assert main_window.checkboxes.move_recycle is not None
    assert main_window.checkboxes.write_graph is not None
    assert main_window.checkboxes.graph_cache is not None
    assert main_window.progress_bar is not None
    assert main_window.buttons.run is not None
    assert main_window.buttons.output is not None
    assert main_window.buttons.delete is not None
    assert main_window.buttons.log is not None
