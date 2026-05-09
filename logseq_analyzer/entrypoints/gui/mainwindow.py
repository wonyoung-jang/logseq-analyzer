"""Logseq Analyzer GUI using PySide6."""

from enum import StrEnum

from PySide6.QtCore import QSettings, Slot
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from logseq_analyzer.entrypoints.gui.components import Buttons, Checkboxes, Inputs, Progress
from logseq_analyzer.entrypoints.gui.worker import AnalysisWorker
from logseq_analyzer.utils.enums import Format


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


class LogseqAnalyzerGUI(QWidget):
    """Main GUI class for the Logseq Analyzer application."""

    def __init__(self) -> None:
        """Initialize the GUI components and layout."""
        super().__init__()
        self.setWindowTitle("Logseq Analyzer")
        self.resize(500, 500)
        self.buttons = Buttons()
        self.inputs = Inputs()
        self.checkboxes = Checkboxes()
        self.progress = Progress()
        self.settings = QSettings("LogseqAnalyzer", "LogseqAnalyzerGUI")
        layout = QVBoxLayout(self)
        layout.addWidget(self.create_graph_folder_layout())
        layout.addWidget(self.create_global_config_layout())
        layout.addWidget(self.inputs)
        layout.addWidget(self.checkboxes)
        layout.addWidget(self.progress)
        layout.addWidget(self.buttons)
        self.load_settings()
        self.connect_signals()

    def connect_signals(self) -> None:
        """Connect signals to their respective slots."""
        self.buttons.run.clicked.connect(self.run_analysis)
        self.buttons.exit.clicked.connect(self.close_analyzer)
        self.inputs.graph_folder.textChanged.connect(self.checkboxes.force_enable_graph_cache)

    @Slot()
    def run_analysis(self) -> None:
        """Run the analysis with the provided arguments."""
        gui_args = {
            Argument.MOVE_UNLINKED_ASSETS: self.checkboxes.move_assets.isChecked(),
            Argument.MOVE_ALL: self.checkboxes.move_all.isChecked(),
            Argument.MOVE_BAK: self.checkboxes.move_bak.isChecked(),
            Argument.MOVE_RECYCLE: self.checkboxes.move_recycle.isChecked(),
            Argument.WRITE_GRAPH: self.checkboxes.write_graph.isChecked(),
            Argument.GRAPH_CACHE: self.checkboxes.graph_cache.isChecked(),
            Argument.GRAPH_FOLDER: self.inputs.graph_folder.text(),
            Argument.GLOBAL_CONFIG: self.inputs.global_config.text(),
            Argument.REPORT_FORMAT: self.inputs.report_format.currentText(),
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
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Graph Folder (Required):"))
        layout.addWidget(self.inputs.graph_folder)
        layout.addWidget(button_graph_folder)
        return widget

    def create_global_config_layout(self) -> QWidget:
        """Create and return the layout for the global config input field."""
        button_global_config = QPushButton("Browse")
        button_global_config.clicked.connect(self.select_global_config_file)
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("Global Config File (Optional):"))
        layout.addWidget(self.inputs.global_config)
        layout.addWidget(button_global_config)
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
        self.settings.setValue(Argument.MOVE_ALL, self.checkboxes.move_all.isChecked())
        self.settings.setValue(Argument.MOVE_UNLINKED_ASSETS, self.checkboxes.move_assets.isChecked())
        self.settings.setValue(Argument.MOVE_BAK, self.checkboxes.move_bak.isChecked())
        self.settings.setValue(Argument.MOVE_RECYCLE, self.checkboxes.move_recycle.isChecked())
        self.settings.setValue(Argument.WRITE_GRAPH, self.checkboxes.write_graph.isChecked())
        self.settings.setValue(Argument.GRAPH_CACHE, self.checkboxes.graph_cache.isChecked())
        self.settings.setValue(Argument.GRAPH_FOLDER, self.inputs.graph_folder.text())
        self.settings.setValue(Argument.GLOBAL_CONFIG, self.inputs.global_config.text())
        self.settings.setValue(Argument.REPORT_FORMAT, self.inputs.report_format.currentText())
        self.settings.setValue(Argument.GEOMETRY, self.saveGeometry())

    def load_settings(self) -> None:
        """Load settings using QSettings."""
        self.checkboxes.move_all.setChecked(bool(self.settings.value(Argument.MOVE_ALL, defaultValue=False, type=bool)))
        self.checkboxes.move_assets.setChecked(
            bool(self.settings.value(Argument.MOVE_UNLINKED_ASSETS, defaultValue=False, type=bool))
        )
        self.checkboxes.move_bak.setChecked(bool(self.settings.value(Argument.MOVE_BAK, defaultValue=False, type=bool)))
        self.checkboxes.move_recycle.setChecked(
            bool(self.settings.value(Argument.MOVE_RECYCLE, defaultValue=False, type=bool))
        )
        self.checkboxes.write_graph.setChecked(
            bool(self.settings.value(Argument.WRITE_GRAPH, defaultValue=False, type=bool))
        )
        self.checkboxes.graph_cache.setChecked(
            bool(self.settings.value(Argument.GRAPH_CACHE, defaultValue=False, type=bool))
        )
        self.inputs.graph_folder.setText(str(self.settings.value(Argument.GRAPH_FOLDER, "", type=str)))
        self.inputs.global_config.setText(str(self.settings.value(Argument.GLOBAL_CONFIG, "", type=str)))
        self.inputs.report_format.setCurrentText(str(self.settings.value(Argument.REPORT_FORMAT, Format.TXT, type=str)))
        self.restoreGeometry(self.settings.value(Argument.GEOMETRY))
