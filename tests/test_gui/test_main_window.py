"""Test the main window of the Logseq Analyzer GUI."""

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QApplication

from logseq_analyzer.gui.main_window import LogseqAnalyzerGUI

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="module")
def app() -> Generator[QApplication]:
    """Fixture for the QApplication."""
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture(scope="module")
def gui(app: QApplication) -> Generator[LogseqAnalyzerGUI]:  # noqa: ARG001
    """Fixture for the LogseqAnalyzerGUI."""
    gui = LogseqAnalyzerGUI()
    yield gui
    gui.close()


@pytest.fixture(scope="module")
def main_window(gui: LogseqAnalyzerGUI) -> Generator[LogseqAnalyzerGUI]:
    """Fixture for the main window of the GUI."""
    gui.show()
    yield gui
    gui.close()


def test_main_window_title(main_window: LogseqAnalyzerGUI) -> None:
    """Test if the main window title is correct."""
    assert main_window.windowTitle() == "Logseq Analyzer"


def test_main_window_initialization(main_window: LogseqAnalyzerGUI) -> None:
    """Test if the main window initializes correctly."""
    assert main_window is not None
    assert main_window.isVisible() is True
    assert main_window.isEnabled() is True
    assert main_window.isActiveWindow() is True


def test_main_window_layout(main_window: LogseqAnalyzerGUI) -> None:
    """Test if the main window layout is set correctly."""
    layout = main_window.layout()
    assert layout is not None
    assert layout.count() > 0

    layout_item_0 = layout.itemAt(0)
    assert layout_item_0 is not None
    assert layout_item_0.widget() is not None


def test_main_window_controls(main_window: LogseqAnalyzerGUI) -> None:
    """Test if the main window controls are present."""
    assert main_window.inputs.graph_folder is not None
    assert main_window.inputs.global_config is not None
    assert main_window.inputs.report_format is not None
    assert main_window.checkboxes.move_assets is not None
    assert main_window.checkboxes.move_bak is not None
    assert main_window.checkboxes.move_recycle is not None
    assert main_window.checkboxes.write_graph is not None
    assert main_window.checkboxes.graph_cache is not None
    assert main_window.progress.progress_bar is not None
    assert main_window.buttons.run is not None
