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
    assert main_window.graph_folder_input is not None
    assert main_window.global_config_input is not None
    assert main_window.report_format_combo is not None
    assert main_window.move_assets_checkbox is not None
    assert main_window.move_bak_checkbox is not None
    assert main_window.move_recycle_checkbox is not None
    assert main_window.write_graph_checkbox is not None
    assert main_window.graph_cache_checkbox is not None
    assert main_window.progress_bar is not None
    assert main_window.run_button is not None
    assert main_window.output_button is not None
    assert main_window.delete_button is not None
    assert main_window.log_button is not None
