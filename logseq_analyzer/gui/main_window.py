"""
Logseq Analyzer GUI using PySide6.
"""

import time
from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..app import run_app
from ..utils.enums import Format

__all__ = [
    "Argument",
    "AnalysisWorker",
    "LogseqAnalyzerGUI",
    "Checkboxes",
    "Buttons",
    "Inputs",
    "Progress",
]


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


class AnalysisWorker(QThread):
    """Thread worker for running the Logseq Analyzer application."""

    progress_signal = Signal(int)
    progress_label = Signal(str)
    finished_signal = Signal(bool, str, float)

    __slots__ = ("args",)

    def __init__(self, args) -> None:
        """Initialize the worker with arguments."""
        super().__init__()
        self.args = args

    def run(self) -> None:
        """Run the Logseq Analyzer application."""
        try:
            start_time = time.perf_counter()

            def update_progress(value, label) -> None:
                self.progress_signal.emit(value)
                self.progress_label.emit(label)

            run_app(**self.args, progress_callback=update_progress)
            self.finished_signal.emit(True, "", time.perf_counter() - start_time)
        except KeyboardInterrupt:
            self.finished_signal.emit(False, "Analysis interrupted by user.", 0)
        except Exception as e:
            self.finished_signal.emit(False, str(e), 0)
            raise


@dataclass
class Checkboxes:
    """Checkboxes for the GUI."""

    move_all: QCheckBox
    move_assets: QCheckBox
    move_bak: QCheckBox
    move_recycle: QCheckBox
    write_graph: QCheckBox
    graph_cache: QCheckBox

    def __post_init__(self) -> None:
        self.move_all.toggled.connect(self.update_move_options)
        self.graph_cache.setEnabled(True)

    def layout(self) -> QVBoxLayout:
        """Creates and returns the layout for checkboxes."""
        layout = QVBoxLayout()
        layout.addWidget(self.move_all)
        layout.addWidget(self.move_assets)
        layout.addWidget(self.move_bak)
        layout.addWidget(self.move_recycle)
        layout.addWidget(self.write_graph)
        layout.addWidget(self.graph_cache)
        return layout

    def update_move_options(self) -> None:
        """Update the state of move options checkboxes based on the main checkbox."""
        if self.move_all.isChecked():
            self.move_assets.setChecked(True)
            self.move_bak.setChecked(True)
            self.move_recycle.setChecked(True)
        else:
            self.move_assets.setChecked(False)
            self.move_bak.setChecked(False)
            self.move_recycle.setChecked(False)

    def force_enable_graph_cache(self) -> None:
        """Force enable and check the graph cache checkbox when the graph folder changes."""
        self.graph_cache.setChecked(True)
        self.graph_cache.setEnabled(False)


@dataclass
class Buttons:
    """Buttons for the GUI."""

    run: QPushButton
    output: QPushButton
    delete: QPushButton
    log: QPushButton

    def __post_init__(self) -> None:
        """Post-initialization to set default values for buttons."""
        self.run.setShortcut("Ctrl+R")
        self.run.setToolTip("Ctrl + R to run analysis")


@dataclass
class Inputs:
    """Input fields for the GUI."""

    graph_folder: QLineEdit
    global_config: QLineEdit
    report_format: QComboBox

    def __post_init__(self) -> None:
        """Post-initialization to set default values for inputs."""
        self.report_format.addItems({Format.TXT, Format.JSON, Format.MD, Format.HTML})

    def report_format_layout(self) -> QFormLayout:
        """Creates and returns the layout for the report format input field."""
        layout = QFormLayout()
        layout.addRow(QLabel("Report Format:"), self.report_format)
        return layout


@dataclass
class Progress:
    """Progress indicators for the GUI."""

    progress_bar: QProgressBar
    label: QLabel

    def __post_init__(self) -> None:
        """Post-initialization to set default values for progress indicators."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def layout(self) -> QFormLayout:
        """Creates and returns the layout for progress indicators."""
        layout = QFormLayout()
        layout.addRow("Progress:", self.progress_bar)
        layout.addRow("Status:", self.label)
        return layout

    def update_bar(self, progress_value: int = 0) -> None:
        """Updates the progress bar for a given phase."""
        self.progress_bar.setValue(progress_value)
        QApplication.processEvents()

    def update_label(self, label: str) -> None:
        """Updates the progress label with a given message."""
        self.label.setText(f"Status: {label}")
        QApplication.processEvents()


class LogseqAnalyzerGUI(QMainWindow):
    """Main GUI class for the Logseq Analyzer application."""

    __slots__ = (
        "inputs",
        "checkboxes",
        "progress",
        "buttons",
        "settings",
        "worker",
    )

    def __init__(self) -> None:
        """Initialize the GUI components and layout."""
        super().__init__()
        self.inputs = None
        self.buttons = None
        self.checkboxes = None
        self.progress = None
        self.worker = None
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.setup_ui_groups()
        self.init_ui()

    def setup_ui_groups(self) -> None:
        """Sets up the UI groups for the main window."""
        self.buttons = Buttons(
            run=QPushButton("Run Analysis"),
            output=QPushButton("Open Output Directory"),
            delete=QPushButton("Open Delete Directory"),
            log=QPushButton("Open Log File"),
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

    def init_ui(self) -> None:
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setWindowTitle("Logseq Analyzer")
        self.resize(500, 500)
        self.setCentralWidget(central_widget)
        self.setup_ui(QGridLayout(central_widget))
        self.load_settings()
        self.inputs.graph_folder.textChanged.connect(self.checkboxes.force_enable_graph_cache)

    def run_analysis(self) -> None:
        """Run the analysis with the provided arguments."""
        _inputs = self.inputs
        _checks = self.checkboxes
        args_gui = {
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
        if not args_gui[Argument.GRAPH_FOLDER]:
            self.show_error("Graph folder is required.")
            return

        self.save_settings()
        self.buttons.run.setEnabled(False)
        self.worker = AnalysisWorker(args_gui)
        self.worker.progress_signal.connect(self.progress.update_bar)
        self.worker.progress_label.connect(self.progress.update_label)
        self.worker.finished_signal.connect(self.handle_analysis_complete)
        self.worker.start()

    def handle_analysis_complete(self, success, error_message, elapsed_time) -> None:
        """Handle completion of analysis"""
        if success:
            self.show_success(f"{elapsed_time:.2f}")
        else:
            self.show_error(f"Analysis failed: {error_message}")

        self.buttons.run.setEnabled(True)
        self.buttons.output.setEnabled(True)
        self.buttons.delete.setEnabled(True)
        self.buttons.log.setEnabled(True)
        self.checkboxes.graph_cache.setEnabled(True)

    def setup_ui(self, main_layout) -> None:
        """Sets up the main user interface layout and elements."""
        form_layout = QFormLayout()
        form_layout.addRow(self.create_graph_folder_layout())
        form_layout.addRow(self.create_global_config_layout())
        form_layout.addRow(self.inputs.report_format_layout())
        form_layout.addRow(self.checkboxes.layout())
        form_layout.addRow(self.progress.layout())

        main_layout.addLayout(form_layout, 0, 0)
        main_layout.addLayout(self.create_buttons_layout(), 1, 0)

    def create_graph_folder_layout(self) -> QFormLayout:
        """Creates and returns the layout for the graph folder input field."""
        graph_folder_button = QPushButton("Browse")
        graph_folder_button.clicked.connect(self.select_graph_folder)

        graph_folder_clear_button = QPushButton("Clear")
        graph_folder_clear_button.clicked.connect(self.inputs.graph_folder.clear)

        graph_folder_layout = QHBoxLayout()
        graph_folder_layout.addWidget(self.inputs.graph_folder)
        graph_folder_layout.addWidget(graph_folder_button)
        graph_folder_layout.addWidget(graph_folder_clear_button)

        layout = QFormLayout()
        layout.addRow(QLabel("Logseq Graph Folder (Required):"), graph_folder_layout)
        return layout

    def create_global_config_layout(self) -> QFormLayout:
        """Creates and returns the layout for the global config input field."""
        global_config_button = QPushButton("Browse")
        global_config_button.clicked.connect(self.select_global_config_file)

        global_config_clear_button = QPushButton("Clear")
        global_config_clear_button.clicked.connect(self.inputs.global_config.clear)

        global_config_layout = QHBoxLayout()
        global_config_layout.addWidget(self.inputs.global_config)
        global_config_layout.addWidget(global_config_button)
        global_config_layout.addWidget(global_config_clear_button)

        layout = QFormLayout()
        layout.addRow(QLabel("Logseq Global Config File (Optional):"), global_config_layout)
        return layout

    def create_buttons_layout(self) -> QHBoxLayout:
        """Creates and returns the layout for all buttons (Run, Exit, Open Directories, Log)."""
        self.buttons.run.clicked.connect(self.run_analysis)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close_analyzer)
        exit_button.setShortcut("Ctrl+W")
        exit_button.setToolTip("Ctrl + W to exit")

        layout = QHBoxLayout()
        layout.addWidget(self.buttons.run)
        layout.addWidget(exit_button)
        return layout

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

    def select_graph_folder(self) -> None:
        """Open a file dialog to select the Logseq graph folder."""
        if folder := QFileDialog.getExistingDirectory(self, "Select Logseq Graph Folder"):
            self.inputs.graph_folder.setText(folder)

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
        _check.move_all.setChecked(get_settings(Argument.MOVE_ALL, False, type=bool))
        _check.move_assets.setChecked(get_settings(Argument.MOVE_UNLINKED_ASSETS, False, type=bool))
        _check.move_bak.setChecked(get_settings(Argument.MOVE_BAK, False, type=bool))
        _check.move_recycle.setChecked(get_settings(Argument.MOVE_RECYCLE, False, type=bool))
        _check.write_graph.setChecked(get_settings(Argument.WRITE_GRAPH, False, type=bool))
        _check.graph_cache.setChecked(get_settings(Argument.GRAPH_CACHE, False, type=bool))
        _inputs.graph_folder.setText(get_settings(Argument.GRAPH_FOLDER, ""))
        _inputs.global_config.setText(get_settings(Argument.GLOBAL_CONFIG, ""))
        _inputs.report_format.setCurrentText(get_settings(Argument.REPORT_FORMAT, Format.TXT))
        self.restoreGeometry(get_settings(Argument.GEOMETRY, b""))
