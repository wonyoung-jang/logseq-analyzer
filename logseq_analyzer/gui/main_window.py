"""
Logseq Analyzer GUI using PySide6.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

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
    finished_signal = Signal(bool, str)

    def __init__(self, args) -> None:
        """Initialize the worker with arguments."""
        super().__init__()
        self.args = args

    def run(self) -> None:
        """Run the Logseq Analyzer application."""
        try:

            def update_progress(value) -> None:
                self.progress_signal.emit(value)

            run_app(**self.args, progress_callback=update_progress)
            self.finished_signal.emit(True, "")
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class LogseqAnalyzerGUI(QMainWindow):
    """Main GUI class for the Logseq Analyzer application."""

    def __init__(self) -> None:
        """Initialize the GUI components and layout."""
        super().__init__()
        self.graph_folder_input = QLineEdit(readOnly=True)
        self.global_config_input = QLineEdit(readOnly=True)
        self.report_format_combo = QComboBox()
        self.move_assets_checkbox = QCheckBox("Move Unlinked Assets to 'to_delete' folder")
        self.move_bak_checkbox = QCheckBox("Move Bak to 'to_delete' folder")
        self.move_recycle_checkbox = QCheckBox("Move Recycle to 'to_delete' folder")
        self.write_graph_checkbox = QCheckBox("Write Full Graph Content (large)")
        self.graph_cache_checkbox = QCheckBox("Reindex Graph Cache")
        self.graph_cache_checkbox.setEnabled(True)
        self.setup_progress_bar = self.create_progress_bar()
        self.run_button = QPushButton("Run Analysis")
        self.output_button = QPushButton("Open Output Directory")
        self.delete_button = QPushButton("Open Delete Directory")
        self.log_button = QPushButton("Open Log File")
        self.setWindowTitle("Logseq Analyzer")
        self.resize(500, 500)
        central_widget = QWidget()
        main_layout = QGridLayout(central_widget)
        self.setCentralWidget(central_widget)
        self.setup_ui(main_layout)
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.load_settings()
        self.graph_folder_input.textChanged.connect(self.force_enable_graph_cache)
        self.worker = None

    def run_analysis(self) -> None:
        """Run the analysis with the provided arguments."""
        args_gui = {
            Arguments.GRAPH_FOLDER.value: self.graph_folder_input.text(),
            Arguments.GLOBAL_CONFIG.value: self.global_config_input.text(),
            Arguments.MOVE_UNLINKED_ASSETS.value: self.move_assets_checkbox.isChecked(),
            Arguments.MOVE_BAK.value: self.move_bak_checkbox.isChecked(),
            Arguments.MOVE_RECYCLE.value: self.move_recycle_checkbox.isChecked(),
            Arguments.WRITE_GRAPH.value: self.write_graph_checkbox.isChecked(),
            Arguments.GRAPH_CACHE.value: self.graph_cache_checkbox.isChecked(),
            Arguments.REPORT_FORMAT.value: self.report_format_combo.currentText(),
        }
        if not args_gui[Arguments.GRAPH_FOLDER.value]:
            self.show_error("Graph folder is required.")
            return

        self.save_settings()
        self.run_button.setEnabled(False)
        self.setup_progress_bar.setValue(0)
        self.worker = AnalysisWorker(args_gui)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.handle_analysis_complete)
        self.worker.start()

    def handle_analysis_complete(self, success, error_message) -> None:
        """Handle completion of analysis"""
        if success:
            success_dialog = QMessageBox(self)
            success_dialog.setIcon(QMessageBox.Information)
            success_dialog.setWindowTitle("Analysis Complete")
            success_dialog.setText("Analysis completed successfully.")
            success_dialog.addButton("Close", QMessageBox.AcceptRole)
            success_dialog.exec()
        else:
            self.show_error(f"Analysis failed: {error_message}")

        self.run_button.setEnabled(True)
        self.output_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.log_button.setEnabled(True)
        self.graph_cache_checkbox.setEnabled(True)

    def setup_ui(self, main_layout) -> None:
        """Sets up the main user interface layout and elements."""
        form_layout = self.create_input_fields_layout()
        main_layout.addLayout(form_layout, 0, 0)

        checkboxes_layout = self.create_checkboxes_layout()
        form_layout.addRow(checkboxes_layout)

        progress_bars_layout = self.create_progress_bars_layout()
        form_layout.addRow(progress_bars_layout)

        buttons_layout = self.create_buttons_layout()
        main_layout.addLayout(buttons_layout, 1, 0)

    def create_input_fields_layout(self) -> QFormLayout:
        """Creates and returns the layout for input fields (graph folder, config file, report format)."""
        form_layout = QFormLayout()

        # --- Graph Folder Input ---
        graph_folder_label = QLabel("Logseq Graph Folder (Required):")
        graph_folder_button = QPushButton("Browse")
        graph_folder_button.clicked.connect(self.select_graph_folder)
        graph_folder_clear_button = QPushButton("Clear")
        graph_folder_clear_button.clicked.connect(self.clear_graph_folder_input)
        graph_folder_hbox = QWidget()
        graph_folder_layout = QHBoxLayout(graph_folder_hbox)
        graph_folder_layout.addWidget(self.graph_folder_input)
        graph_folder_layout.addWidget(graph_folder_button)
        graph_folder_layout.addWidget(graph_folder_clear_button)
        form_layout.addRow(graph_folder_label, graph_folder_hbox)

        # --- Global Config File Input ---
        global_config_label = QLabel("Logseq Global Config File (Optional):")
        global_config_button = QPushButton("Browse")
        global_config_button.clicked.connect(self.select_global_config_file)
        global_config_clear_button = QPushButton("Clear")
        global_config_clear_button.clicked.connect(self.clear_global_config_input)
        global_config_hbox = QWidget()
        global_config_layout = QHBoxLayout(global_config_hbox)
        global_config_layout.addWidget(self.global_config_input)
        global_config_layout.addWidget(global_config_button)
        global_config_layout.addWidget(global_config_clear_button)
        form_layout.addRow(global_config_label, global_config_hbox)

        # --- Report Format Dropdown ---
        report_format_label = QLabel("Report Format:")
        self.report_format_combo.addItems(
            [
                Format.TXT.value,
                Format.JSON.value,
                Format.MD.value,
                Format.HTML.value,
            ]
        )
        form_layout.addRow(report_format_label, self.report_format_combo)

        return form_layout

    def clear_graph_folder_input(self) -> None:
        """Clear the graph folder input field."""
        self.graph_folder_input.clear()

    def clear_global_config_input(self) -> None:
        """Clear the global config input field."""
        self.global_config_input.clear()

    def create_checkboxes_layout(self) -> QVBoxLayout:
        """Creates and returns the layout for checkboxes."""
        checkboxes_layout = QVBoxLayout()
        checkboxes_layout.addWidget(self.move_assets_checkbox)
        checkboxes_layout.addWidget(self.move_bak_checkbox)
        checkboxes_layout.addWidget(self.move_recycle_checkbox)
        checkboxes_layout.addWidget(self.write_graph_checkbox)
        checkboxes_layout.addWidget(self.graph_cache_checkbox)
        return checkboxes_layout

    def force_enable_graph_cache(self) -> None:
        """Force enable and check the graph cache checkbox when the graph folder changes."""
        self.graph_cache_checkbox.setChecked(True)
        self.graph_cache_checkbox.setEnabled(False)

    def create_progress_bars_layout(self) -> QFormLayout:
        """Creates and returns the layout for progress bars."""
        progress_bars_layout = QFormLayout()
        progress_bars_layout.addRow("Progress:", self.setup_progress_bar)
        return progress_bars_layout

    def create_progress_bar(self) -> QProgressBar:
        """Create a progress bar."""
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        return progress_bar

    def create_buttons_layout(self) -> QVBoxLayout:
        """Creates and returns the layout for all buttons (Run, Exit, Open Directories, Log)."""
        buttons_layout = QVBoxLayout()
        button_layout_primary = QHBoxLayout()
        button_layout_secondary = QHBoxLayout()
        buttons_layout.addLayout(button_layout_primary)
        buttons_layout.addLayout(button_layout_secondary)

        self.run_button.clicked.connect(self.run_analysis)
        self.run_button.setShortcut("Ctrl+R")
        self.run_button.setToolTip("Ctrl+R to run analysis")
        button_layout_primary.addWidget(self.run_button)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close_analyzer)
        exit_button.setShortcut("Ctrl+W")
        exit_button.setToolTip("Ctrl+W to exit")
        button_layout_primary.addWidget(exit_button)

        # --- Secondary Buttons ---
        self.output_button.clicked.connect(self.open_output_directory)
        self.output_button.setEnabled(False)
        button_layout_secondary.addWidget(self.output_button)

        self.delete_button.clicked.connect(self.open_delete_directory)
        self.delete_button.setEnabled(False)
        button_layout_secondary.addWidget(self.delete_button)

        self.log_button.clicked.connect(self.open_log_file)
        self.log_button.setEnabled(False)
        button_layout_secondary.addWidget(self.log_button)

        return buttons_layout

    def close_analyzer(self) -> None:
        """Close the application."""
        self.save_settings()
        self.close()

    def open_output_directory(self) -> None:
        """Open the output directory in the file explorer."""
        od = OutputDirectory()
        output_dir = od.path
        self._open_path(output_dir)

    def open_delete_directory(self) -> None:
        """Open the delete directory in the file explorer."""
        dd = DeleteDirectory()
        delete_dir = dd.path
        self._open_path(delete_dir)

    def open_log_file(self) -> None:
        """Open the log file in the default text editor."""
        lf = LogFile()
        log_file = lf.path
        self._open_path(log_file)

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

    def update_progress(self, progress_value=0) -> None:
        """Updates the progress bar for a given phase."""
        progress_bar = self.setup_progress_bar
        if progress_bar:
            progress_bar.setValue(progress_value)
            QApplication.processEvents()

    def show_error(self, message) -> None:
        """Show an error message in a dialog."""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec()

    def select_graph_folder(self) -> None:
        """Open a file dialog to select the Logseq graph folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Logseq Graph Folder")
        if folder:
            self.graph_folder_input.setText(folder)

    def select_global_config_file(self) -> None:
        """Open a file dialog to select the Logseq global config file."""
        file, _ = QFileDialog.getOpenFileName(self, "Select Logseq Global Config File", "", "EDN Files (*.edn)")
        if file:
            self.global_config_input.setText(file)

    def save_settings(self) -> None:
        """Save current settings using QSettings."""
        self.settings.setValue(Arguments.GRAPH_FOLDER.value, self.graph_folder_input.text())
        self.settings.setValue(Arguments.GLOBAL_CONFIG.value, self.global_config_input.text())
        self.settings.setValue(Arguments.MOVE_UNLINKED_ASSETS.value, self.move_assets_checkbox.isChecked())
        self.settings.setValue(Arguments.MOVE_BAK.value, self.move_bak_checkbox.isChecked())
        self.settings.setValue(Arguments.MOVE_RECYCLE.value, self.move_recycle_checkbox.isChecked())
        self.settings.setValue(Arguments.WRITE_GRAPH.value, self.write_graph_checkbox.isChecked())
        self.settings.setValue(Arguments.GRAPH_CACHE.value, self.graph_cache_checkbox.isChecked())
        self.settings.setValue(Arguments.REPORT_FORMAT.value, self.report_format_combo.currentText())
        self.settings.setValue(Arguments.GEOMETRY.value, self.saveGeometry())

    def load_settings(self) -> None:
        """Load settings using QSettings."""
        self.graph_folder_input.setText(self.settings.value(Arguments.GRAPH_FOLDER.value, ""))
        self.global_config_input.setText(self.settings.value(Arguments.GLOBAL_CONFIG.value, ""))
        self.move_assets_checkbox.setChecked(
            self.settings.value(Arguments.MOVE_UNLINKED_ASSETS.value, False, type=bool)
        )
        self.move_bak_checkbox.setChecked(self.settings.value(Arguments.MOVE_BAK.value, False, type=bool))
        self.move_recycle_checkbox.setChecked(self.settings.value(Arguments.MOVE_RECYCLE.value, False, type=bool))
        self.write_graph_checkbox.setChecked(self.settings.value(Arguments.WRITE_GRAPH.value, False, type=bool))
        self.graph_cache_checkbox.setChecked(self.settings.value(Arguments.GRAPH_CACHE.value, False, type=bool))
        self.report_format_combo.setCurrentText(self.settings.value(Arguments.REPORT_FORMAT.value, Format.TXT.value))
        self.restoreGeometry(self.settings.value(Arguments.GEOMETRY.value, b""))


def resource_path(relative_path) -> Any:
    """Get the absolute path to the resource."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return Path(os.path.abspath(".")) / relative_path
