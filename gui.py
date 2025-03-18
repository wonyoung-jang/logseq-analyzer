import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QProgressBar,
    QComboBox,
)
from PySide6.QtCore import QSettings, QTimer

from src.app import run_app


class LogseqAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logseq Analyzer")

        # Central Widget and Layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Form Layout for Input Fields
        form_layout = QFormLayout()
        main_layout.addLayout(form_layout)

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

        self.reporting_progress_bar = QProgressBar()
        self.reporting_progress_bar.setRange(0, 100)
        self.reporting_progress_bar.setValue(0)
        form_layout.addRow("Reporting:", self.reporting_progress_bar)

        self.namespaces_progress_bar = QProgressBar()
        self.namespaces_progress_bar.setRange(0, 100)
        self.namespaces_progress_bar.setValue(0)
        form_layout.addRow("Namespaces:", self.namespaces_progress_bar)

        self.move_files_progress_bar = QProgressBar()
        self.move_files_progress_bar.setRange(0, 100)
        self.move_files_progress_bar.setValue(0)
        form_layout.addRow("Move Files:", self.move_files_progress_bar)

        # Buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        self.run_button.setShortcut("Ctrl+R")
        self.run_button.setToolTip("Ctrl+R to run analysis")
        button_layout.addWidget(self.run_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.exit_button.setShortcut("Ctrl+W")
        self.exit_button.setToolTip("Ctrl+W to exit")
        button_layout.addWidget(self.exit_button)

        self.setCentralWidget(central_widget)
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        self.load_settings()

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
        self.reporting_progress_bar.setValue(0)
        self.namespaces_progress_bar.setValue(0)
        self.move_files_progress_bar.setValue(0)
        QApplication.processEvents()

        try:
            run_app(**args_gui, gui_instance=self)
            remaining_seconds = 10
            success_dialog = QMessageBox(self)
            success_dialog.setIcon(QMessageBox.Information)
            success_dialog.setWindowTitle("Analysis Complete")
            success_dialog.setText(f"Analysis complete! The app will close in {remaining_seconds} seconds.")
            success_dialog.addButton("Close", QMessageBox.AcceptRole)
            timer = QTimer(self)

            def update_dialog():
                nonlocal remaining_seconds
                remaining_seconds -= 1
                if remaining_seconds > 0:
                    success_dialog.setText(f"Analysis complete! The app will close in {remaining_seconds} seconds.")
                else:
                    timer.stop()
                    success_dialog.accept()

            timer.timeout.connect(update_dialog)
            timer.start(1000)
            success_dialog.exec()
            self.close()
        except KeyboardInterrupt:
            self.show_error("Analysis interrupted by user.")
            self.close()
        except Exception as e:
            self.show_error(f"Analysis failed: {e}")
        finally:
            self.run_button.setEnabled(True)

    def update_progress(self, phase_name, progress_value):
        """Updates the progress bar for a given phase."""
        progress_bar = None
        if phase_name == "setup":
            progress_bar = self.setup_progress_bar
        elif phase_name == "process_files":
            progress_bar = self.process_files_progress_bar
        elif phase_name == "reporting":
            progress_bar = self.reporting_progress_bar
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

    def load_settings(self):
        """Load settings using QSettings."""
        self.graph_folder_input.setText(self.settings.value("graph_folder", ""))
        self.global_config_input.setText(self.settings.value("global_config_file", ""))
        self.move_assets_checkbox.setChecked(self.settings.value("move_assets", False, type=bool))
        self.move_bak_checkbox.setChecked(self.settings.value("move_bak", False, type=bool))
        self.move_recycle_checkbox.setChecked(self.settings.value("move_recycle", False, type=bool))
        self.write_graph_checkbox.setChecked(self.settings.value("write_graph", False, type=bool))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = LogseqAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
