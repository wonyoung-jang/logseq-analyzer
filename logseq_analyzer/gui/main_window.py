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

    def create_layout(self) -> QVBoxLayout:
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


@dataclass
class Inputs:
    """Input fields for the GUI."""

    graph_folder: QLineEdit
    global_config: QLineEdit
    report_format: QComboBox

    def __post_init__(self) -> None:
        """Post-initialization to set default values for inputs."""
        self.report_format.addItems({Format.TXT, Format.JSON, Format.MD, Format.HTML})


class LogseqAnalyzerGUI(QMainWindow):
    """Main GUI class for the Logseq Analyzer application."""

    __slots__ = (
        "inputs",
        "checkboxes",
        "progress_bar",
        "buttons",
        "settings",
        "worker",
    )

    def __init__(self) -> None:
        """Initialize the GUI components and layout."""
        super().__init__()
        self.inputs = Inputs(
            graph_folder=QLineEdit(readOnly=True),
            global_config=QLineEdit(readOnly=True),
            report_format=QComboBox(),
        )
        self.buttons = Buttons(
            run=QPushButton("Run Analysis"),
            output=QPushButton("Open Output Directory"),
            delete=QPushButton("Open Delete Directory"),
            log=QPushButton("Open Log File"),
        )
        self.checkboxes = Checkboxes(
            move_all=QCheckBox("Enable all move options"),
            move_assets=QCheckBox("Move Unlinked Assets to 'to_delete' folder"),
            move_bak=QCheckBox("Move Bak to 'to_delete' folder"),
            move_recycle=QCheckBox("Move Recycle to 'to_delete' folder"),
            write_graph=QCheckBox("Write Full Graph Content (large)"),
            graph_cache=QCheckBox("Reindex Graph Cache"),
        )
        self.progress_bar = QProgressBar(self)
        self.progress_label = QLabel("Status: Ready")
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.worker = None
        self.init_ui()
        self.inputs.graph_folder.textChanged.connect(self.checkboxes.force_enable_graph_cache)

    def init_ui(self) -> None:
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setWindowTitle("Logseq Analyzer")
        self.resize(500, 500)
        self.setCentralWidget(central_widget)
        self.setup_ui(QGridLayout(central_widget))
        self.load_settings()

    def run_analysis(self) -> None:
        """Run the analysis with the provided arguments."""
        args_gui = {
            Argument.GRAPH_FOLDER: self.inputs.graph_folder.text(),
            Argument.GLOBAL_CONFIG: self.inputs.global_config.text(),
            Argument.MOVE_UNLINKED_ASSETS: self.checkboxes.move_assets.isChecked(),
            Argument.MOVE_ALL: self.checkboxes.move_all.isChecked(),
            Argument.MOVE_BAK: self.checkboxes.move_bak.isChecked(),
            Argument.MOVE_RECYCLE: self.checkboxes.move_recycle.isChecked(),
            Argument.WRITE_GRAPH: self.checkboxes.write_graph.isChecked(),
            Argument.GRAPH_CACHE: self.checkboxes.graph_cache.isChecked(),
            Argument.REPORT_FORMAT: self.inputs.report_format.currentText(),
        }
        if not args_gui[Argument.GRAPH_FOLDER]:
            self.show_error("Graph folder is required.")
            return

        self.save_settings()
        self.buttons.run.setEnabled(False)
        self.progress_bar.setValue(0)
        self.worker = AnalysisWorker(args_gui)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.progress_label.connect(self.update_progress_label)
        self.worker.finished_signal.connect(self.handle_analysis_complete)
        self.worker.start()

    def handle_analysis_complete(self, success, error_message, elapsed_time) -> None:
        """Handle completion of analysis"""
        if success:
            success_dialog = QMessageBox(self)
            success_dialog.setIcon(QMessageBox.Icon.Information)
            success_dialog.setWindowTitle("Analysis Complete")
            success_dialog.setText(f"Analysis completed successfully in {elapsed_time:.2f} seconds.")
            success_dialog.addButton("Close", QMessageBox.ButtonRole.AcceptRole)
            success_dialog.exec()
        else:
            self.show_error(f"Analysis failed: {error_message}")

        self.buttons.run.setEnabled(True)
        self.buttons.output.setEnabled(True)
        self.buttons.delete.setEnabled(True)
        self.buttons.log.setEnabled(True)
        self.checkboxes.graph_cache.setEnabled(True)

    def setup_ui(self, main_layout) -> None:
        """Sets up the main user interface layout and elements."""
        form_layout = self._create_input_fields_layout()
        main_layout.addLayout(form_layout, 0, 0)

        form_layout.addRow(self.checkboxes.create_layout())

        progress_bars_layout = self._create_progress_bars_layout()
        form_layout.addRow(progress_bars_layout)

        buttons_layout = self._create_buttons_layout()
        main_layout.addLayout(buttons_layout, 1, 0)

    def _create_input_fields_layout(self) -> QFormLayout:
        """Creates and returns the layout for input fields (graph folder, config file, report format)."""

        # --- Graph Folder Input ---
        graph_folder_label = QLabel("Logseq Graph Folder (Required):")
        graph_folder_button = QPushButton("Browse")
        graph_folder_button.clicked.connect(self.select_graph_folder)
        graph_folder_clear_button = QPushButton("Clear")
        graph_folder_clear_button.clicked.connect(self.inputs.graph_folder.clear)

        graph_folder_layout = QHBoxLayout()
        graph_folder_layout.addWidget(self.inputs.graph_folder)
        graph_folder_layout.addWidget(graph_folder_button)
        graph_folder_layout.addWidget(graph_folder_clear_button)

        # --- Global Config File Input ---
        global_config_label = QLabel("Logseq Global Config File (Optional):")
        global_config_button = QPushButton("Browse")
        global_config_button.clicked.connect(self.select_global_config_file)
        global_config_clear_button = QPushButton("Clear")
        global_config_clear_button.clicked.connect(self.inputs.global_config.clear)

        global_config_layout = QHBoxLayout()
        global_config_layout.addWidget(self.inputs.global_config)
        global_config_layout.addWidget(global_config_button)
        global_config_layout.addWidget(global_config_clear_button)

        # --- Report Format Dropdown ---
        report_format_label = QLabel("Report Format:")

        form_layout = QFormLayout()
        form_layout.addRow(graph_folder_label, graph_folder_layout)
        form_layout.addRow(global_config_label, global_config_layout)
        form_layout.addRow(report_format_label, self.inputs.report_format)
        return form_layout

    def _create_progress_bars_layout(self) -> QFormLayout:
        """Creates and returns the layout for progress bars."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_bars_layout = QFormLayout()
        progress_bars_layout.addRow("Progress:", self.progress_bar)
        progress_bars_layout.addRow("Status:", self.progress_label)
        return progress_bars_layout

    def _create_buttons_layout(self) -> QVBoxLayout:
        """Creates and returns the layout for all buttons (Run, Exit, Open Directories, Log)."""
        self.buttons.run.clicked.connect(self.run_analysis)
        self.buttons.run.setShortcut("Ctrl+R")
        self.buttons.run.setToolTip("Ctrl + R to run analysis")

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close_analyzer)
        exit_button.setShortcut("Ctrl+W")
        exit_button.setToolTip("Ctrl + W to exit")

        buttons_layout = QGridLayout()
        buttons_layout.addWidget(self.buttons.run, 0, 0)
        buttons_layout.addWidget(exit_button, 0, 2)
        return buttons_layout

    def close_analyzer(self) -> None:
        """Close the application."""
        self.save_settings()
        self.close()

    def update_progress(self, progress_value: int = 0) -> None:
        """Updates the progress bar for a given phase."""
        if self.progress_bar:
            self.progress_bar.setValue(progress_value)
            QApplication.processEvents()

    def update_progress_label(self, label: str) -> None:
        """Updates the progress label with a given message."""
        if self.progress_label:
            self.progress_label.setText(f"Status: {label}")
            QApplication.processEvents()

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
        _checkboxes = self.checkboxes
        set_settings(Argument.MOVE_ALL, _checkboxes.move_all.isChecked())
        set_settings(Argument.MOVE_UNLINKED_ASSETS, _checkboxes.move_assets.isChecked())
        set_settings(Argument.MOVE_BAK, _checkboxes.move_bak.isChecked())
        set_settings(Argument.MOVE_RECYCLE, _checkboxes.move_recycle.isChecked())
        set_settings(Argument.WRITE_GRAPH, _checkboxes.write_graph.isChecked())
        set_settings(Argument.GRAPH_CACHE, _checkboxes.graph_cache.isChecked())
        set_settings(Argument.GRAPH_FOLDER, _inputs.graph_folder.text())
        set_settings(Argument.GLOBAL_CONFIG, _inputs.global_config.text())
        set_settings(Argument.REPORT_FORMAT, _inputs.report_format.currentText())
        set_settings(Argument.GEOMETRY, self.saveGeometry())

    def load_settings(self) -> None:
        """Load settings using QSettings."""
        get_settings = self.settings.value
        _inputs = self.inputs
        _checkboxes = self.checkboxes
        _checkboxes.move_all.setChecked(get_settings(Argument.MOVE_ALL, False, type=bool))
        _checkboxes.move_assets.setChecked(get_settings(Argument.MOVE_UNLINKED_ASSETS, False, type=bool))
        _checkboxes.move_bak.setChecked(get_settings(Argument.MOVE_BAK, False, type=bool))
        _checkboxes.move_recycle.setChecked(get_settings(Argument.MOVE_RECYCLE, False, type=bool))
        _checkboxes.write_graph.setChecked(get_settings(Argument.WRITE_GRAPH, False, type=bool))
        _checkboxes.graph_cache.setChecked(get_settings(Argument.GRAPH_CACHE, False, type=bool))
        _inputs.graph_folder.setText(get_settings(Argument.GRAPH_FOLDER, ""))
        _inputs.global_config.setText(get_settings(Argument.GLOBAL_CONFIG, ""))
        _inputs.report_format.setCurrentText(get_settings(Argument.REPORT_FORMAT, Format.TXT))
        self.restoreGeometry(get_settings(Argument.GEOMETRY, b""))
