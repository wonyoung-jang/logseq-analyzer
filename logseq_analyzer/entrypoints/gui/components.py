"""UI components for the Logseq Analyzer GUI."""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from logseq_analyzer.utils.enums import Format


class Checkboxes(QWidget):
    """Checkboxes for the GUI."""

    def __init__(self) -> None:
        """Post-initialization to set default values for checkboxes."""
        super().__init__()
        self.move_all = QCheckBox("Enable all move options")
        self.move_assets = QCheckBox("Move Unlinked Assets to 'to_delete' folder")
        self.move_bak = QCheckBox("Move Bak to 'to_delete' folder")
        self.move_recycle = QCheckBox("Move Recycle to 'to_delete' folder")
        self.write_graph = QCheckBox("Write Full Graph Content (large)")
        self.graph_cache = QCheckBox("Reindex Graph Cache")
        self.graph_cache.setEnabled(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.move_all)
        layout.addWidget(self.move_assets)
        layout.addWidget(self.move_bak)
        layout.addWidget(self.move_recycle)
        layout.addWidget(self.write_graph)
        layout.addWidget(self.graph_cache)
        self.move_all.toggled.connect(self.update_move_options)

    @Slot()
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

    @Slot()
    def force_enable_graph_cache(self) -> None:
        """Force enable and check the graph cache checkbox when the graph folder changes."""
        self.graph_cache.setChecked(True)
        self.graph_cache.setEnabled(False)


class Buttons(QWidget):
    """Buttons for the GUI."""

    def __init__(self) -> None:
        """Post-initialization to set default values for buttons."""
        super().__init__()
        self.run = QPushButton("Run Analysis")
        self.run.setShortcut("Ctrl+R")
        self.run.setToolTip("Ctrl + R to run analysis")
        self.exit = QPushButton("Exit")
        self.exit.setShortcut("Ctrl+W")
        self.exit.setToolTip("Ctrl + W to exit")
        layout = QHBoxLayout(self)
        layout.addWidget(self.run)
        layout.addWidget(self.exit)


class Inputs(QWidget):
    """Input fields for the GUI."""

    def __init__(self) -> None:
        """Post-initialization to set default values for inputs."""
        super().__init__()
        self.graph_folder = QLineEdit(readOnly=True, clearButtonEnabled=True)
        self.global_config = QLineEdit(readOnly=True, clearButtonEnabled=True)
        self.report_format = QComboBox()
        self.report_format.addItems((Format.TXT, Format.JSON, Format.MD, Format.HTML))
        layout = QFormLayout(self)
        layout.addRow(QLabel("Report Format:"), self.report_format)


class Progress(QWidget):
    """Progress indicators for the GUI."""

    def __init__(self) -> None:
        """Initialize the progress indicators."""
        super().__init__()
        self.progress_bar = QProgressBar(minimum=0, maximum=100, value=0)
        self.label = QLabel("Ready")
        layout = QFormLayout(self)
        layout.addRow("Progress:", self.progress_bar)
        layout.addRow("Status:", self.label)

    @Slot()
    def update_bar(self, progress_value: int = 0) -> None:
        """Update the progress bar for a given phase."""
        self.progress_bar.setValue(progress_value)

    @Slot()
    def update_label(self, label: str) -> None:
        """Update the progress label with a given message."""
        self.label.setText(f"{label}")
