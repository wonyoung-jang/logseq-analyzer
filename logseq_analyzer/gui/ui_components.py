"""UI components for the Logseq Analyzer GUI."""

from dataclasses import dataclass

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

from ..utils.enums import Format


@dataclass(slots=True, weakref_slot=True)
class Checkboxes(QWidget):
    """Checkboxes for the GUI."""

    move_all: QCheckBox
    move_assets: QCheckBox
    move_bak: QCheckBox
    move_recycle: QCheckBox
    write_graph: QCheckBox
    graph_cache: QCheckBox

    def __post_init__(self) -> None:
        """Post-initialization to set default values for checkboxes."""
        super().__init__()
        self.move_all.toggled.connect(self.update_move_options)
        self.graph_cache.setEnabled(True)
        self.initialize_layout()

    def initialize_layout(self) -> None:
        """Create and return the layout for checkboxes."""
        layout = QVBoxLayout()
        layout.addWidget(self.move_all)
        layout.addWidget(self.move_assets)
        layout.addWidget(self.move_bak)
        layout.addWidget(self.move_recycle)
        layout.addWidget(self.write_graph)
        layout.addWidget(self.graph_cache)
        self.setLayout(layout)

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


@dataclass(slots=True)
class Buttons(QWidget):
    """Buttons for the GUI."""

    run: QPushButton
    exit: QPushButton

    def __post_init__(self) -> None:
        """Post-initialization to set default values for buttons."""
        super().__init__()
        self.run.setShortcut("Ctrl+R")
        self.run.setToolTip("Ctrl + R to run analysis")
        self.exit.setShortcut("Ctrl+W")
        self.exit.setToolTip("Ctrl + W to exit")
        self.initialize_layout()

    def initialize_layout(self) -> None:
        """Create and return the layout for buttons."""
        layout = QHBoxLayout()
        layout.addWidget(self.run)
        layout.addWidget(self.exit)
        self.setLayout(layout)


@dataclass(slots=True)
class Inputs(QWidget):
    """Input fields for the GUI."""

    graph_folder: QLineEdit
    global_config: QLineEdit
    report_format: QComboBox

    def __post_init__(self) -> None:
        """Post-initialization to set default values for inputs."""
        super().__init__()
        self.report_format.addItems((Format.TXT, Format.JSON, Format.MD, Format.HTML))
        self.initialize_layout()

    def initialize_layout(self) -> None:
        """Create and return the layout for the report format input field."""
        layout = QFormLayout()
        layout.addRow(QLabel("Report Format:"), self.report_format)
        self.setLayout(layout)


@dataclass(slots=True, weakref_slot=True)
class Progress(QWidget):
    """Progress indicators for the GUI."""

    progress_bar: QProgressBar
    label: QLabel

    def __post_init__(self) -> None:
        """Post-initialization to set default values for progress indicators."""
        super().__init__()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.initialize_layout()

    def initialize_layout(self) -> None:
        """Create and return the layout for progress indicators."""
        layout = QFormLayout()
        layout.addRow("Progress:", self.progress_bar)
        layout.addRow("Status:", self.label)
        self.setLayout(layout)

    @Slot()
    def update_bar(self, progress_value: int = 0) -> None:
        """Update the progress bar for a given phase."""
        self.progress_bar.setValue(progress_value)

    @Slot()
    def update_label(self, label: str) -> None:
        """Update the progress label with a given message."""
        self.label.setText(f"Status: {label}")
