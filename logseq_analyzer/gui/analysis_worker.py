"""Worker thread for running the Logseq Analyzer application."""

import time

from PySide6.QtCore import QThread, Signal

from ..app import run_app

__all__ = [
    "AnalysisWorker",
]


class AnalysisWorker(QThread):
    """Thread worker for running the Logseq Analyzer application."""

    progress_signal = Signal(int)
    progress_label = Signal(str)
    finished_signal = Signal(bool, str, float)

    __slots__ = ("gui_args",)

    def __init__(self, args) -> None:
        """Initialize the worker with arguments."""
        super().__init__()
        self.gui_args = args

    def run(self) -> None:
        """Run the Logseq Analyzer application."""
        try:
            start_time = time.perf_counter()
            run_app(**self.gui_args, progress_callback=self.update_progress)
            self.finished_signal.emit(True, "", time.perf_counter() - start_time)
        except KeyboardInterrupt:
            self.finished_signal.emit(False, "Analysis interrupted by user.", 0)
        except Exception as e:
            self.finished_signal.emit(False, str(e), 0)
            raise

    def update_progress(self, value: int, label: str) -> None:
        """Update the progress bar and label during analysis."""
        self.progress_signal.emit(value)
        self.progress_label.emit(label)
