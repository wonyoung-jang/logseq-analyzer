"""
Logseq Analyzer GUI using PySide6.
"""

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QSettings
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

from src.app import run_app
from src.reporting import write_output
from src.config_loader import get_config


CONFIG = get_config()


class LogseqAnalyzerGUI(QMainWindow):
    """Main GUI class for the Logseq Analyzer application."""

    def __init__(self):
        """Initialize the GUI components and layout."""
        super().__init__()
        self.setWindowTitle("Logseq Analyzer")
        self.setGeometry(500, 500, 500, 500)
        self.output_dir = CONFIG.get("DEFAULT", "OUTPUT_DIR")

        # Central Widget and Layout
        central_widget = QWidget()
        main_layout = QGridLayout(central_widget)
        self.setCentralWidget(central_widget)

        self.setup_ui(main_layout)

        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.load_settings()

    def setup_ui(self, main_layout):
        """Sets up the main user interface layout and elements."""
        form_layout = self.create_input_fields_layout()
        main_layout.addLayout(form_layout, 0, 0)

        checkboxes_layout = self.create_checkboxes_layout()
        form_layout.addRow(checkboxes_layout)

        progress_bars_layout = self.create_progress_bars_layout()
        form_layout.addRow(progress_bars_layout)

        buttons_layout = self.create_buttons_layout()
        main_layout.addLayout(buttons_layout, 1, 0)

    def create_graph_cache_layout(self) -> QFormLayout:
        """Creates and returns the layout for graph cache settings."""
        graph_cache_layout = QFormLayout()
        self.graph_cache_checkbox = QCheckBox("Use Graph Cache")
        self.graph_cache_checkbox.setChecked(CONFIG.getboolean("DEFAULT", "USE_GRAPH_CACHE"))
        graph_cache_layout.addRow(self.graph_cache_checkbox)
        return graph_cache_layout

    def create_input_fields_layout(self) -> QFormLayout:
        """Creates and returns the layout for input fields (graph folder, config file, report format)."""
        form_layout = QFormLayout()

        # --- Graph Folder Input ---
        graph_folder_label = QLabel("Logseq Graph Folder (Required):")
        self.graph_folder_input = QLineEdit()
        graph_folder_button = QPushButton("Browse")
        graph_folder_button.clicked.connect(self.select_graph_folder)
        graph_folder_hbox = QWidget()
        graph_folder_layout = QHBoxLayout(graph_folder_hbox)
        graph_folder_layout.addWidget(self.graph_folder_input)
        graph_folder_layout.addWidget(graph_folder_button)
        form_layout.addRow(graph_folder_label, graph_folder_hbox)

        # --- Global Config File Input ---
        global_config_label = QLabel("Logseq Global Config File (Optional):")
        self.global_config_input = QLineEdit()
        global_config_button = QPushButton("Browse")
        global_config_button.clicked.connect(self.select_global_config_file)
        global_config_hbox = QWidget()
        global_config_layout = QHBoxLayout(global_config_hbox)
        global_config_layout.addWidget(self.global_config_input)
        global_config_layout.addWidget(global_config_button)
        form_layout.addRow(global_config_label, global_config_hbox)

        # --- Report Format Dropdown ---
        report_format_label = QLabel("Report Format:")
        self.report_format_combo = QComboBox()
        self.report_format_combo.addItems([".txt", ".json", ".md"])
        form_layout.addRow(report_format_label, self.report_format_combo)

        return form_layout

    def create_checkboxes_layout(self) -> QVBoxLayout:
        """Creates and returns the layout for checkboxes."""
        checkboxes_layout = QVBoxLayout()
        self.move_assets_checkbox = QCheckBox("Move Unlinked Assets to 'to_delete' folder")
        self.move_bak_checkbox = QCheckBox("Move Bak to 'to_delete' folder")
        self.move_recycle_checkbox = QCheckBox("Move Recycle to 'to_delete' folder")
        self.write_graph_checkbox = QCheckBox("Write Full Graph Content (large)")
        checkboxes_layout.addWidget(self.move_assets_checkbox)
        checkboxes_layout.addWidget(self.move_bak_checkbox)
        checkboxes_layout.addWidget(self.move_recycle_checkbox)
        checkboxes_layout.addWidget(self.write_graph_checkbox)
        return checkboxes_layout

    def create_progress_bars_layout(self) -> QFormLayout:
        """Creates and returns the layout for progress bars."""
        progress_bars_layout = QFormLayout()
        self.setup_progress_bar = self.create_progress_bar()
        self.process_files_progress_bar = self.create_progress_bar()
        self.summary_progress_bar = self.create_progress_bar()
        self.move_files_progress_bar = self.create_progress_bar()
        progress_bars_layout.addRow("Setup:", self.setup_progress_bar)
        progress_bars_layout.addRow("Process Files:", self.process_files_progress_bar)
        progress_bars_layout.addRow("Summarizing:", self.summary_progress_bar)
        progress_bars_layout.addRow("Move Files:", self.move_files_progress_bar)
        return progress_bars_layout

    def create_progress_bar(self):
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

        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        self.run_button.setShortcut("Ctrl+R")
        self.run_button.setToolTip("Ctrl+R to run analysis")
        button_layout_primary.addWidget(self.run_button)

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        exit_button.setShortcut("Ctrl+W")
        exit_button.setToolTip("Ctrl+W to exit")
        button_layout_primary.addWidget(exit_button)

        # --- Secondary Buttons ---
        self.output_button = QPushButton("Open Output Directory")
        self.output_button.clicked.connect(self.open_output_directory)
        self.output_button.setEnabled(False)
        button_layout_secondary.addWidget(self.output_button)

        self.delete_button = QPushButton("Open Delete Directory")
        self.delete_button.clicked.connect(self.open_delete_directory)
        self.delete_button.setEnabled(False)
        button_layout_secondary.addWidget(self.delete_button)

        self.log_button = QPushButton("Open Log File")
        self.log_button.clicked.connect(self.open_log_file)
        self.log_button.setEnabled(False)
        button_layout_secondary.addWidget(self.log_button)

        return buttons_layout

    def open_output_directory(self):
        """Open the output directory in the file explorer."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        if os.path.exists(self.output_dir):
            self.output_dir = os.path.abspath(self.output_dir)
            if sys.platform.startswith("win"):
                os.startfile(self.output_dir)
            elif sys.platform.startswith("darwin"):
                subprocess.call(["open", self.output_dir])
            else:
                subprocess.call(["xdg-open", self.output_dir])
        else:
            self.show_error("Output directory not found.")

    def open_delete_directory(self):
        """Open the delete directory in the file explorer."""
        delete_dir = CONFIG.get("DEFAULT", "TO_DELETE_DIR")
        if not os.path.exists(delete_dir):
            os.makedirs(delete_dir)
        if os.path.exists(delete_dir):
            delete_dir = os.path.abspath(delete_dir)
            if sys.platform.startswith("win"):
                os.startfile(delete_dir)
            elif sys.platform.startswith("darwin"):
                subprocess.call(["open", delete_dir])
            else:
                subprocess.call(["xdg-open", delete_dir])
        else:
            self.show_error("Delete directory not found.")

    def open_log_file(self):
        """Open the log file in the default text editor."""
        log_file_path = Path(self.output_dir) / CONFIG.get("DEFAULT", "LOG_FILE")
        if os.path.exists(log_file_path):
            if sys.platform.startswith("win"):
                os.startfile(log_file_path)
            elif sys.platform.startswith("darwin"):
                subprocess.call(["open", log_file_path])
            else:
                subprocess.call(["xdg-open", log_file_path])
        else:
            self.show_error("Log file not found.")

    def run_analysis(self):
        """Run the analysis with the provided arguments."""
        args_gui = {
            "graph_folder": self.graph_folder_input.text(),
            "global_config_file": self.global_config_input.text(),
            "move_assets": self.move_assets_checkbox.isChecked(),
            "move_bak": self.move_bak_checkbox.isChecked(),
            "move_recycle": self.move_recycle_checkbox.isChecked(),
            "write_graph": self.write_graph_checkbox.isChecked(),
            "report_format": self.report_format_combo.currentText(),
        }
        if not args_gui["graph_folder"]:
            self.show_error("Graph folder is required.")
            return

        self.save_settings()
        self.run_button.setEnabled(False)

        # Reset progress bars before starting
        self.setup_progress_bar.setValue(0)
        self.process_files_progress_bar.setValue(0)
        self.summary_progress_bar.setValue(0)
        self.move_files_progress_bar.setValue(0)
        QApplication.processEvents()

        try:
            output_data = run_app(**args_gui, gui_instance=self)

            output_meta = [
                "___meta___alphanum_dict_ns",
                "___meta___alphanum_dict",
                "___meta___config_edn_data",
                "___meta___config_patterns",
                "___meta___content_patterns",
                "___meta___graph_content",
                "___meta___graph_data",
                "___meta___target_dirs",
                "all_refs",
                "dangling_dict",
                "dangling_links",
                "set_all_prop_values_builtin",
                "set_all_prop_values_user",
                "sorted_all_props_builtin",
                "sorted_all_props_user",
            ]
            output_summaries = [
                "summary_data_subsets",
                "summary_sorted_all",
            ]
            output_namespaces = [
                "summary_namespaces",
            ]
            output_assets = [
                "moved_files",
                "assets_backlinked",
                "assets_not_backlinked",
            ]

            for key, items in output_data.items():
                if key in output_meta:
                    write_output(self.output_dir, key, items, CONFIG.get("OUTPUT_DIRS", "META"))
                elif key in output_summaries:
                    for summary, data in items.items():
                        write_output(self.output_dir, summary, data, CONFIG.get("OUTPUT_DIRS", "SUMMARY"))
                elif key in output_namespaces:
                    for summary, data in items.items():
                        write_output(self.output_dir, summary, data, CONFIG.get("OUTPUT_DIRS", "NAMESPACE"))
                elif key in output_assets:
                    write_output(self.output_dir, key, items, CONFIG.get("OUTPUT_DIRS", "ASSETS"))

            success_dialog = QMessageBox(self)
            success_dialog.setIcon(QMessageBox.Information)
            success_dialog.setWindowTitle("Analysis Complete")
            success_dialog.setText("Analysis completed successfully.")
            success_dialog.addButton("Close", QMessageBox.AcceptRole)
            success_dialog.exec()
        except KeyboardInterrupt:
            self.show_error("Analysis interrupted by user.")
            self.close()
        finally:
            self.run_button.setEnabled(True)
            self.output_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.log_button.setEnabled(True)

    def update_progress(self, phase_name, progress_value):
        """Updates the progress bar for a given phase."""
        progress_bar = None
        if phase_name == "setup":
            progress_bar = self.setup_progress_bar
        elif phase_name == "process_files":
            progress_bar = self.process_files_progress_bar
        elif phase_name == "summary":
            progress_bar = self.summary_progress_bar
        elif phase_name == "move_files":
            progress_bar = self.move_files_progress_bar

        if progress_bar:
            progress_bar.setValue(progress_value)
            QApplication.processEvents()

    def show_error(self, message):
        """Show an error message in a dialog."""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec()

    def select_graph_folder(self):
        """Open a file dialog to select the Logseq graph folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Logseq Graph Folder")
        if folder:
            self.graph_folder_input.setText(folder)

    def select_global_config_file(self):
        """Open a file dialog to select the Logseq global config file."""
        file, _ = QFileDialog.getOpenFileName(self, "Select Logseq Global Config File", "", "EDN Files (*.edn)")
        if file:
            self.global_config_input.setText(file)

    def save_settings(self):
        """Save current settings using QSettings."""
        self.settings.setValue("graph_folder", self.graph_folder_input.text())
        self.settings.setValue("global_config_file", self.global_config_input.text())
        self.settings.setValue("move_assets", self.move_assets_checkbox.isChecked())
        self.settings.setValue("move_bak", self.move_bak_checkbox.isChecked())
        self.settings.setValue("move_recycle", self.move_recycle_checkbox.isChecked())
        self.settings.setValue("write_graph", self.write_graph_checkbox.isChecked())
        self.settings.setValue("report_format", self.report_format_combo.currentText())
        self.settings.setValue("geometry", self.saveGeometry())

    def load_settings(self):
        """Load settings using QSettings."""
        self.graph_folder_input.setText(self.settings.value("graph_folder", ""))
        self.global_config_input.setText(self.settings.value("global_config_file", ""))
        self.move_assets_checkbox.setChecked(self.settings.value("move_assets", False, type=bool))
        self.move_bak_checkbox.setChecked(self.settings.value("move_bak", False, type=bool))
        self.move_recycle_checkbox.setChecked(self.settings.value("move_recycle", False, type=bool))
        self.write_graph_checkbox.setChecked(self.settings.value("write_graph", False, type=bool))
        self.report_format_combo.setCurrentText(self.settings.value("report_format", ".txt"))
        self.restoreGeometry(self.settings.value("geometry", b""))


if __name__ == "__main__":
    app = QApplication()
    gui = LogseqAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
