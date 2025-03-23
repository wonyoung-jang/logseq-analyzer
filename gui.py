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

from src import config

from src.app import run_app
from src.reporting import write_output


class LogseqAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logseq Analyzer")
        self.setGeometry(500, 500, 500, 500)

        # Central Widget and Layout
        central_widget = QWidget()
        main_layout = QGridLayout(central_widget)

        # Form Layout for Input Fields
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout, 0, 0)

        # Logseq Graph Folder Input
        self.graph_folder_label = QLabel("Logseq Graph Folder (Required):")
        self.graph_folder_input = QLineEdit()
        self.graph_folder_button = QPushButton("Browse")
        self.graph_folder_button.clicked.connect(self.select_graph_folder)
        graph_folder_hbox = QWidget()
        graph_folder_layout = QHBoxLayout(graph_folder_hbox)
        graph_folder_layout.addWidget(self.graph_folder_input)
        graph_folder_layout.addWidget(self.graph_folder_button)
        form_layout.addRow(self.graph_folder_label, graph_folder_hbox)

        # Logseq Global Config File Input
        self.global_config_label = QLabel("Logseq Global Config File (Optional):")
        self.global_config_input = QLineEdit()
        self.global_config_button = QPushButton("Browse")
        self.global_config_button.clicked.connect(self.select_global_config_file)
        global_config_hbox = QWidget()
        global_config_layout = QHBoxLayout(global_config_hbox)
        global_config_layout.addWidget(self.global_config_input)
        global_config_layout.addWidget(self.global_config_button)
        form_layout.addRow(self.global_config_label, global_config_hbox)

        # Report Format dropdown (txt, json)
        self.report_format_label = QLabel("Report Format:")
        self.report_format_combo = QComboBox()
        self.report_format_combo.addItems([".txt", ".json"])
        form_layout.addRow(self.report_format_label, self.report_format_combo)

        # Checkboxes
        self.move_assets_checkbox = QCheckBox("Move Unlinked Assets to 'to_delete' folder")
        form_layout.addRow(self.move_assets_checkbox)
        self.move_bak_checkbox = QCheckBox("Move Bak to 'to_delete' folder")
        form_layout.addRow(self.move_bak_checkbox)
        self.move_recycle_checkbox = QCheckBox("Move Recycle to 'to_delete' folder")
        form_layout.addRow(self.move_recycle_checkbox)
        self.write_graph_checkbox = QCheckBox("Write Full Graph Content (large)")
        form_layout.addRow(self.write_graph_checkbox)

        # Progress Bars
        self.setup_progress_bar = QProgressBar()
        self.setup_progress_bar.setRange(0, 100)
        self.setup_progress_bar.setValue(0)
        form_layout.addRow("Setup:", self.setup_progress_bar)

        self.process_files_progress_bar = QProgressBar()
        self.process_files_progress_bar.setRange(0, 100)
        self.process_files_progress_bar.setValue(0)
        form_layout.addRow("Process Files:", self.process_files_progress_bar)

        self.summary_progress_bar = QProgressBar()
        self.summary_progress_bar.setRange(0, 100)
        self.summary_progress_bar.setValue(0)
        form_layout.addRow("Summarizing:", self.summary_progress_bar)

        self.namespaces_progress_bar = QProgressBar()
        self.namespaces_progress_bar.setRange(0, 100)
        self.namespaces_progress_bar.setValue(0)
        form_layout.addRow("Namespaces:", self.namespaces_progress_bar)

        self.move_files_progress_bar = QProgressBar()
        self.move_files_progress_bar.setRange(0, 100)
        self.move_files_progress_bar.setValue(0)
        form_layout.addRow("Move Files:", self.move_files_progress_bar)

        # Buttons
        button_layout = QVBoxLayout()
        button_layout_primary = QHBoxLayout()
        button_layout_secondary = QHBoxLayout()
        button_layout.addLayout(button_layout_primary)
        button_layout.addLayout(button_layout_secondary)
        main_layout.addLayout(button_layout, 1, 0)

        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        self.run_button.setShortcut("Ctrl+R")
        self.run_button.setToolTip("Ctrl+R to run analysis")
        button_layout_primary.addWidget(self.run_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setShortcut("Ctrl+W")
        self.exit_button.setToolTip("Ctrl+W to exit")
        button_layout_primary.addWidget(self.exit_button)

        # Button to open output directory
        self.output_button = QPushButton("Open Output Directory")
        self.output_button.clicked.connect(self.open_output_directory)
        self.output_button.setEnabled(False)  # Initially disabled
        button_layout_secondary.addWidget(self.output_button)

        # Button to open to_delete directory
        self.delete_button = QPushButton("Open Delete Directory")
        self.delete_button.clicked.connect(self.open_delete_directory)
        self.delete_button.setEnabled(False)
        button_layout_secondary.addWidget(self.delete_button)

        # Button to open log file
        self.log_button = QPushButton("Open Log File")
        self.log_button.clicked.connect(self.open_log_file)
        self.log_button.setEnabled(False)  # Initially disabled
        button_layout_secondary.addWidget(self.log_button)

        self.setCentralWidget(central_widget)
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.load_settings()

    def open_output_directory(self):
        """Open the output directory in the file explorer."""
        output_dir = config.DEFAULT_OUTPUT_DIR
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if os.path.exists(output_dir):
            output_dir = os.path.abspath(output_dir)
            if sys.platform.startswith("win"):
                os.startfile(output_dir)
            elif sys.platform.startswith("darwin"):
                subprocess.call(["open", output_dir])
            else:
                subprocess.call(["xdg-open", output_dir])
        else:
            self.show_error("Output directory not found.")

    def open_delete_directory(self):
        """Open the delete directory in the file explorer."""
        delete_dir = config.DEFAULT_TO_DELETE_DIR
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
        log_file_path = Path(config.DEFAULT_OUTPUT_DIR) / config.DEFAULT_LOG_FILE
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
        self.namespaces_progress_bar.setValue(0)
        self.move_files_progress_bar.setValue(0)
        QApplication.processEvents()

        try:
            output_data = run_app(**args_gui, gui_instance=self)

            output_meta = [
                "alphanum_dict",
                "alphanum_dict_ns",
                "dangling_links",
                "config_edn_data",
                "target_dirs",
                "graph_data",
                "graph_content",
                "content_patterns",
                "config_patterns",
                "all_refs",
                "dangling_dict",
                "set_all_prop_values_builtin",
                "set_all_prop_values_user",
                "sorted_all_props_builtin",
                "sorted_all_props_user",
            ]
            output_summaries = [
                "___summary_global",
                "summary_data_subsets",
                "summary_sorted_all",
            ]
            output_namespaces = [
                "___summary_global_namespaces",
                "summary_namespaces",
            ]
            output_assets = [
                "moved_files",
                "assets_backlinked",
                "assets_not_backlinked",
            ]

            for key, items in output_data.items():
                if key in output_meta:
                    write_output(config.DEFAULT_OUTPUT_DIR, key, items, config.OUTPUT_DIR_META)
                elif key in output_summaries:
                    if key == "___summary_global":
                        write_output(config.DEFAULT_OUTPUT_DIR, key, items, config.OUTPUT_DIR_SUMMARY)
                    else:
                        for summary, data in items.items():
                            write_output(config.DEFAULT_OUTPUT_DIR, summary, data, config.OUTPUT_DIR_SUMMARY)
                elif key in output_namespaces:
                    if key == "___summary_global_namespaces":
                        write_output(config.DEFAULT_OUTPUT_DIR, key, items, config.OUTPUT_DIR_NAMESPACE)
                    else:
                        for summary, data in items.items():
                            write_output(config.DEFAULT_OUTPUT_DIR, summary, data, config.OUTPUT_DIR_NAMESPACE)
                elif key in output_assets:
                    write_output(config.DEFAULT_OUTPUT_DIR, key, items, config.OUTPUT_DIR_ASSETS)

            success_dialog = QMessageBox(self)
            success_dialog.setIcon(QMessageBox.Information)
            success_dialog.setWindowTitle("Analysis Complete")
            success_dialog.setText("Analysis completed successfully.")
            success_dialog.addButton("Close", QMessageBox.AcceptRole)
            success_dialog.exec()
        except KeyboardInterrupt:
            self.show_error("Analysis interrupted by user.")
            self.close()
        except Exception as e:
            self.show_error(f"Analysis failed: {e}")
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
        elif phase_name == "namespaces":
            progress_bar = self.namespaces_progress_bar
        elif phase_name == "move_files":
            progress_bar = self.move_files_progress_bar

        if progress_bar:
            progress_bar.setValue(progress_value)
            QApplication.processEvents()

    def show_error(self, message):
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText(message)
        error_dialog.exec()

    def select_graph_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Logseq Graph Folder")
        if folder:
            self.graph_folder_input.setText(folder)

    def select_global_config_file(self):
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
        self.settings.setValue("geometry", self.saveGeometry())

    def load_settings(self):
        """Load settings using QSettings."""
        self.graph_folder_input.setText(self.settings.value("graph_folder", ""))
        self.global_config_input.setText(self.settings.value("global_config_file", ""))
        self.move_assets_checkbox.setChecked(self.settings.value("move_assets", False, type=bool))
        self.move_bak_checkbox.setChecked(self.settings.value("move_bak", False, type=bool))
        self.move_recycle_checkbox.setChecked(self.settings.value("move_recycle", False, type=bool))
        self.write_graph_checkbox.setChecked(self.settings.value("write_graph", False, type=bool))
        self.restoreGeometry(self.settings.value("geometry", b""))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = LogseqAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
