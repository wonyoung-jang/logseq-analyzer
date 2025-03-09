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
)
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

        # Checkboxes
        self.move_assets_checkbox = QCheckBox("Move Unlinked Assets to 'to_delete' folder")
        form_layout.addRow(self.move_assets_checkbox)
        self.move_bak_checkbox = QCheckBox("Move Bak to 'to_delete' folder")
        form_layout.addRow(self.move_bak_checkbox)
        self.move_recycle_checkbox = QCheckBox("Move Recycle to 'to_delete' folder")
        form_layout.addRow(self.move_recycle_checkbox)
        self.write_graph_checkbox = QCheckBox("Write Full Graph Content (large)")
        form_layout.addRow(self.write_graph_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)
        self.run_button = QPushButton("Run Analysis")
        self.run_button.clicked.connect(self.run_analysis)
        button_layout.addWidget(self.run_button)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.exit_button)

        self.setCentralWidget(central_widget)

    def run_analysis(self):
        args_gui = {
            "graph_folder": self.graph_folder_input.text(),
            "global_config_file": self.global_config_input.text(),
            "move_assets": self.move_assets_checkbox.isChecked(),
            "move_bak": self.move_bak_checkbox.isChecked(),
            "move_recycle": self.move_recycle_checkbox.isChecked(),
            "write_graph": self.write_graph_checkbox.isChecked(),
        }
        if not args_gui["graph_folder"]:
            self.show_error("Graph folder is required.")
            return

        # Call the run_app function with the provided parameters
        run_app(**args_gui)
        # Show success message when analysis is complete
        success_dialog = QMessageBox(self)
        success_dialog.setIcon(QMessageBox.Information)
        success_dialog.setWindowTitle("Success")
        success_dialog.setText("Analysis completed successfully.")
        success_dialog.exec()

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = LogseqAnalyzerGUI()
    gui.show()
    sys.exit(app.exec())
