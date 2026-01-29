"""Logseq Analyzer GUI using PySide6."""

from dataclasses import dataclass, field
from enum import StrEnum

from PySide6.QtCore import QSettings, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.enums import Format
from .analysis_worker import AnalysisWorker
from .ui_components import Buttons, Checkboxes, Inputs, Progress


class Argument(StrEnum):
    """Arguments for the Logseq Analyzer."""

    GEOMETRY = "geometry"
    GLOBAL_CONFIG = "global_config"
    GRAPH_CACHE = "graph_cache"
    GRAPH_FOLDER = "graph_folder"
    MOVE_ALL = "move_all"
    MOVE_BAK = "move_bak"
    MOVE_RECYCLE = "move_recycle"
    MOVE_UNLINKED_ASSETS = "move_unlinked_assets"
    REPORT_FORMAT = "report_format"
    WRITE_GRAPH = "write_graph"


@dataclass(slots=True)
class LogseqAnalyzerGUI(QWidget):
    """Main GUI class for the Logseq Analyzer application."""

    inputs: Inputs = field(init=False)
    buttons: Buttons = field(init=False)
    checkboxes: Checkboxes = field(init=False)
    progress: Progress = field(init=False)
    worker: AnalysisWorker = field(init=False)
    settings: QSettings = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the GUI components and layout."""
        super().__init__()
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.setup_ui_objects()
        self.initialize_layout()
        self.connect_signals()
        self.load_settings()

    def setup_ui_objects(self) -> None:
        """Set up the UI groups for the main window."""
        self.buttons = Buttons(
            run=QPushButton("Run Analysis"),
            exit=QPushButton("Exit"),
        )
        self.inputs = Inputs(
            graph_folder=QLineEdit(readOnly=True),
            global_config=QLineEdit(readOnly=True),
            report_format=QComboBox(),
        )
        self.checkboxes = Checkboxes(
            move_all=QCheckBox("Enable all move options"),
            move_assets=QCheckBox("Move Unlinked Assets to 'to_delete' folder"),
            move_bak=QCheckBox("Move Bak to 'to_delete' folder"),
            move_recycle=QCheckBox("Move Recycle to 'to_delete' folder"),
            write_graph=QCheckBox("Write Full Graph Content (large)"),
            graph_cache=QCheckBox("Reindex Graph Cache"),
        )
        self.progress = Progress(progress_bar=QProgressBar(self), label=QLabel("Status: Ready"))

    def initialize_layout(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.addWidget(self.create_graph_folder_layout())
        layout.addWidget(self.create_global_config_layout())
        layout.addWidget(self.inputs)
        layout.addWidget(self.checkboxes)
        layout.addWidget(self.progress)
        layout.addWidget(self.buttons)
        self.setWindowTitle("Logseq Analyzer")
        self.resize(500, 500)

    def connect_signals(self) -> None:
        """Connect signals to their respective slots."""
        self.buttons.run.clicked.connect(self.run_analysis)
        self.buttons.exit.clicked.connect(self.close_analyzer)
        self.inputs.graph_folder.textChanged.connect(self.checkboxes.force_enable_graph_cache)

    @Slot()
    def run_analysis(self) -> None:
        """Run the analysis with the provided arguments."""
        _inputs = self.inputs
        _checks = self.checkboxes
        gui_args = {
            Argument.MOVE_UNLINKED_ASSETS: _checks.move_assets.isChecked(),
            Argument.MOVE_ALL: _checks.move_all.isChecked(),
            Argument.MOVE_BAK: _checks.move_bak.isChecked(),
            Argument.MOVE_RECYCLE: _checks.move_recycle.isChecked(),
            Argument.WRITE_GRAPH: _checks.write_graph.isChecked(),
            Argument.GRAPH_CACHE: _checks.graph_cache.isChecked(),
            Argument.GRAPH_FOLDER: _inputs.graph_folder.text(),
            Argument.GLOBAL_CONFIG: _inputs.global_config.text(),
            Argument.REPORT_FORMAT: _inputs.report_format.currentText(),
        }
        if not gui_args[Argument.GRAPH_FOLDER]:
            self.show_error("Graph folder is required.")
            return

        self.save_settings()
        self.buttons.run.setEnabled(False)
        self.worker = AnalysisWorker(gui_args)
        self.worker.progress_signal.connect(self.progress.update_bar)
        self.worker.progress_label.connect(self.progress.update_label)
        self.worker.finished_signal.connect(self.handle_analysis_complete)
        self.worker.start()

    @Slot()
    def handle_analysis_complete(self, error_message: str, elapsed_time: float, success: bool) -> None:  # noqa: FBT001
        """Handle completion of analysis."""
        if success:
            self.show_success(f"{elapsed_time:.2f}")
        else:
            self.show_error(f"Analysis failed: {error_message}")
        self.buttons.run.setEnabled(True)
        self.checkboxes.graph_cache.setEnabled(True)

    def create_graph_folder_layout(self) -> QWidget:
        """Create and return the layout for the graph folder input field."""
        button_graph_folder = QPushButton("Browse")
        button_graph_folder.clicked.connect(self.select_graph_folder)
        button_clear = QPushButton("Clear")
        button_clear.clicked.connect(self.inputs.graph_folder.clear)
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Graph Folder (Required):"))
        layout.addWidget(self.inputs.graph_folder)
        layout.addWidget(button_graph_folder)
        layout.addWidget(button_clear)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def create_global_config_layout(self) -> QWidget:
        """Create and return the layout for the global config input field."""
        button_global_config = QPushButton("Browse")
        button_global_config.clicked.connect(self.select_global_config_file)
        button_clear = QPushButton("Clear")
        button_clear.clicked.connect(self.inputs.global_config.clear)
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Global Config File (Optional):"))
        layout.addWidget(self.inputs.global_config)
        layout.addWidget(button_global_config)
        layout.addWidget(button_clear)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    @Slot()
    def close_analyzer(self) -> None:
        """Close the application."""
        self.save_settings()
        self.close()

    def show_success(self, time_elapsed: str) -> None:
        """Show a success message in a dialog."""
        success_dialog = QMessageBox(self)
        success_dialog.setIcon(QMessageBox.Icon.Information)
        success_dialog.setWindowTitle("Success - Analysis Complete")
        success_dialog.setText(f"Analysis completed successfully in {time_elapsed} seconds.")
        success_dialog.addButton("Close", QMessageBox.ButtonRole.AcceptRole)
        success_dialog.exec()

    def show_error(self, message: str) -> None:
        """Show an error message in a dialog."""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec()

    @Slot()
    def select_graph_folder(self) -> None:
        """Open a file dialog to select the Logseq graph folder."""
        if folder := QFileDialog.getExistingDirectory(self, "Select Logseq Graph Folder"):
            self.inputs.graph_folder.setText(folder)

    @Slot()
    def select_global_config_file(self) -> None:
        """Open a file dialog to select the Logseq global config file."""
        file, _ = QFileDialog.getOpenFileName(self, "Select Logseq Global Config File", "", "EDN Files (*.edn)")
        if file:
            self.inputs.global_config.setText(file)

    def save_settings(self) -> None:
        """Save current settings using QSettings."""
        set_settings = self.settings.setValue
        _inputs = self.inputs
        _check = self.checkboxes
        set_settings(Argument.MOVE_ALL, _check.move_all.isChecked())
        set_settings(Argument.MOVE_UNLINKED_ASSETS, _check.move_assets.isChecked())
        set_settings(Argument.MOVE_BAK, _check.move_bak.isChecked())
        set_settings(Argument.MOVE_RECYCLE, _check.move_recycle.isChecked())
        set_settings(Argument.WRITE_GRAPH, _check.write_graph.isChecked())
        set_settings(Argument.GRAPH_CACHE, _check.graph_cache.isChecked())
        set_settings(Argument.GRAPH_FOLDER, _inputs.graph_folder.text())
        set_settings(Argument.GLOBAL_CONFIG, _inputs.global_config.text())
        set_settings(Argument.REPORT_FORMAT, _inputs.report_format.currentText())
        set_settings(Argument.GEOMETRY, self.saveGeometry())

    def load_settings(self) -> None:
        """Load settings using QSettings."""
        get_settings = self.settings.value
        _inputs = self.inputs
        _check = self.checkboxes
        _check.move_all.setChecked(bool(get_settings(Argument.MOVE_ALL, defaultValue=False, type=bool)))
        _check.move_assets.setChecked(bool(get_settings(Argument.MOVE_UNLINKED_ASSETS, defaultValue=False, type=bool)))
        _check.move_bak.setChecked(bool(get_settings(Argument.MOVE_BAK, defaultValue=False, type=bool)))
        _check.move_recycle.setChecked(bool(get_settings(Argument.MOVE_RECYCLE, defaultValue=False, type=bool)))
        _check.write_graph.setChecked(bool(get_settings(Argument.WRITE_GRAPH, defaultValue=False, type=bool)))
        _check.graph_cache.setChecked(bool(get_settings(Argument.GRAPH_CACHE, defaultValue=False, type=bool)))
        _inputs.graph_folder.setText(str(get_settings(Argument.GRAPH_FOLDER, "", type=str)))
        _inputs.global_config.setText(str(get_settings(Argument.GLOBAL_CONFIG, "", type=str)))
        _inputs.report_format.setCurrentText(str(get_settings(Argument.REPORT_FORMAT, Format.TXT, type=str)))
        self.restoreGeometry(get_settings(Argument.GEOMETRY))
