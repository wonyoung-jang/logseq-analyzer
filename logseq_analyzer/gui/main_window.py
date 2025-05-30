"""
Logseq Analyzer GUI using PySide6.
"""

import os
import subprocess
import sys
import time
from dataclasses import dataclass

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
from ..io.filesystem import DeleteDirectory, LogFile, OutputDirectory
from ..utils.enums import Arguments, Format


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
            curr_time = time.time()

            def update_progress(value, label) -> None:
                self.progress_signal.emit(value)
                self.progress_label.emit(label)

            run_app(**self.args, progress_callback=update_progress)
            self.finished_signal.emit(True, "", time.time() - curr_time)
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
        self.checkboxes.graph_cache.setEnabled(True)
        self.progress_bar = self.create_progress_bar()
        self.progress_text = QLabel("Status: Ready")
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.worker = None
        self.init_ui()
        self.inputs.graph_folder.textChanged.connect(self.force_enable_graph_cache)

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
            Arguments.GRAPH_FOLDER.value: self.inputs.graph_folder.text(),
            Arguments.GLOBAL_CONFIG.value: self.inputs.global_config.text(),
            Arguments.MOVE_UNLINKED_ASSETS.value: self.checkboxes.move_assets.isChecked(),
            Arguments.MOVE_ALL.value: self.checkboxes.move_all.isChecked(),
            Arguments.MOVE_BAK.value: self.checkboxes.move_bak.isChecked(),
            Arguments.MOVE_RECYCLE.value: self.checkboxes.move_recycle.isChecked(),
            Arguments.WRITE_GRAPH.value: self.checkboxes.write_graph.isChecked(),
            Arguments.GRAPH_CACHE.value: self.checkboxes.graph_cache.isChecked(),
            Arguments.REPORT_FORMAT.value: self.inputs.report_format.currentText(),
        }
        if not args_gui[Arguments.GRAPH_FOLDER.value]:
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

        checkboxes_layout = self._create_checkboxes_layout()
        form_layout.addRow(checkboxes_layout)

        progress_bars_layout = self._create_progress_bars_layout()
        form_layout.addRow(progress_bars_layout)

        buttons_layout = self._create_buttons_layout()
        main_layout.addLayout(buttons_layout, 1, 0)

    def _create_input_fields_layout(self) -> QFormLayout:
        """Creates and returns the layout for input fields (graph folder, config file, report format)."""
        form_layout = QFormLayout()

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
        form_layout.addRow(graph_folder_label, graph_folder_layout)

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
        form_layout.addRow(global_config_label, global_config_layout)

        # --- Report Format Dropdown ---
        report_format_label = QLabel("Report Format:")
        self.inputs.report_format.addItems(
            (
                Format.TXT.value,
                Format.JSON.value,
                Format.MD.value,
                Format.HTML.value,
            )
        )
        form_layout.addRow(report_format_label, self.inputs.report_format)

        return form_layout

    def _create_checkboxes_layout(self) -> QVBoxLayout:
        """Creates and returns the layout for checkboxes."""
        checkboxes_layout = QVBoxLayout()
        checkboxes_layout.addWidget(self.checkboxes.move_all)
        checkboxes_layout.addWidget(self.checkboxes.move_assets)
        checkboxes_layout.addWidget(self.checkboxes.move_bak)
        checkboxes_layout.addWidget(self.checkboxes.move_recycle)
        checkboxes_layout.addWidget(self.checkboxes.write_graph)
        checkboxes_layout.addWidget(self.checkboxes.graph_cache)
        self.checkboxes.move_all.toggled.connect(self.update_move_options)
        return checkboxes_layout

    def update_move_options(self) -> None:
        """Update the state of move options checkboxes based on the main checkbox."""
        if self.checkboxes.move_all.isChecked():
            self.checkboxes.move_assets.setChecked(True)
            self.checkboxes.move_bak.setChecked(True)
            self.checkboxes.move_recycle.setChecked(True)
        else:
            self.checkboxes.move_assets.setChecked(False)
            self.checkboxes.move_bak.setChecked(False)
            self.checkboxes.move_recycle.setChecked(False)

    def force_enable_graph_cache(self) -> None:
        """Force enable and check the graph cache checkbox when the graph folder changes."""
        self.checkboxes.graph_cache.setChecked(True)
        self.checkboxes.graph_cache.setEnabled(False)

    def _create_progress_bars_layout(self) -> QFormLayout:
        """Creates and returns the layout for progress bars."""
        progress_bars_layout = QFormLayout()
        progress_bars_layout.addRow("Progress:", self.progress_bar)
        progress_bars_layout.addRow("Status:", self.progress_text)
        return progress_bars_layout

    def create_progress_bar(self) -> QProgressBar:
        """Create a progress bar."""
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        return progress_bar

    def _create_buttons_layout(self) -> QVBoxLayout:
        """Creates and returns the layout for all buttons (Run, Exit, Open Directories, Log)."""
        buttons_layout = QGridLayout()

        self.buttons.run.clicked.connect(self.run_analysis)
        self.buttons.run.setShortcut("Ctrl+R")
        self.buttons.run.setToolTip("Ctrl+R to run analysis")
        buttons_layout.addWidget(self.buttons.run, 0, 0, 1, 2)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close_analyzer)
        exit_button.setShortcut("Ctrl+W")
        exit_button.setToolTip("Ctrl+W to exit")
        buttons_layout.addWidget(exit_button, 0, 2, 1, 1)

        # --- Secondary Buttons ---
        self.buttons.output.clicked.connect(self._open_output_dir)
        self.buttons.output.setEnabled(False)
        buttons_layout.addWidget(self.buttons.output, 1, 0)

        self.buttons.delete.clicked.connect(self._open_delete_dir)
        self.buttons.delete.setEnabled(False)
        buttons_layout.addWidget(self.buttons.delete, 1, 1)

        self.buttons.log.clicked.connect(self._open_log_file)
        self.buttons.log.setEnabled(False)
        buttons_layout.addWidget(self.buttons.log, 1, 2)

        return buttons_layout

    def close_analyzer(self) -> None:
        """Close the application."""
        self.save_settings()
        self.close()

    def _open_output_dir(self) -> None:
        """Open the output directory in the file explorer."""
        self._open_path(OutputDirectory().path)

    def _open_delete_dir(self) -> None:
        """Open the delete directory in the file explorer."""
        self._open_path(DeleteDirectory().path)

    def _open_log_file(self) -> None:
        """Open the log file in the default text editor."""
        self._open_path(LogFile().path)

    def _open_path(self, path) -> None:
        """Open a path in the file explorer."""
        if path.exists():
            path = path.resolve()
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform.startswith("darwin"):
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        else:
            self.show_error(f"Path not found: {path}")

    def update_progress(self, progress_value: int = 0) -> None:
        """Updates the progress bar for a given phase."""
        if self.progress_bar:
            self.progress_bar.setValue(progress_value)
            QApplication.processEvents()

    def update_progress_label(self, label: str) -> None:
        """Updates the progress label with a given message."""
        if self.progress_text:
            self.progress_text.setText(f"Status: {label}")
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
        self.settings.setValue(Arguments.GRAPH_FOLDER.value, self.inputs.graph_folder.text())
        self.settings.setValue(Arguments.GLOBAL_CONFIG.value, self.inputs.global_config.text())
        self.settings.setValue(Arguments.MOVE_ALL.value, self.checkboxes.move_all.isChecked())
        self.settings.setValue(Arguments.MOVE_UNLINKED_ASSETS.value, self.checkboxes.move_assets.isChecked())
        self.settings.setValue(Arguments.MOVE_BAK.value, self.checkboxes.move_bak.isChecked())
        self.settings.setValue(Arguments.MOVE_RECYCLE.value, self.checkboxes.move_recycle.isChecked())
        self.settings.setValue(Arguments.WRITE_GRAPH.value, self.checkboxes.write_graph.isChecked())
        self.settings.setValue(Arguments.GRAPH_CACHE.value, self.checkboxes.graph_cache.isChecked())
        self.settings.setValue(Arguments.REPORT_FORMAT.value, self.inputs.report_format.currentText())
        self.settings.setValue(Arguments.GEOMETRY.value, self.saveGeometry())

    def load_settings(self) -> None:
        """Load settings using QSettings."""
        self.inputs.graph_folder.setText(self.settings.value(Arguments.GRAPH_FOLDER.value, ""))
        self.inputs.global_config.setText(self.settings.value(Arguments.GLOBAL_CONFIG.value, ""))
        self.checkboxes.move_all.setChecked(self.settings.value(Arguments.MOVE_ALL.value, False, type=bool))
        self.checkboxes.move_assets.setChecked(
            self.settings.value(Arguments.MOVE_UNLINKED_ASSETS.value, False, type=bool)
        )
        self.checkboxes.move_bak.setChecked(self.settings.value(Arguments.MOVE_BAK.value, False, type=bool))
        self.checkboxes.move_recycle.setChecked(self.settings.value(Arguments.MOVE_RECYCLE.value, False, type=bool))
        self.checkboxes.write_graph.setChecked(self.settings.value(Arguments.WRITE_GRAPH.value, False, type=bool))
        self.checkboxes.graph_cache.setChecked(self.settings.value(Arguments.GRAPH_CACHE.value, False, type=bool))
        self.inputs.report_format.setCurrentText(self.settings.value(Arguments.REPORT_FORMAT.value, Format.TXT.value))
        self.restoreGeometry(self.settings.value(Arguments.GEOMETRY.value, b""))
