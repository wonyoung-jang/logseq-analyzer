"""Worker thread for running the Logseq Analyzer application."""

from __future__ import annotations

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
    finished_signal = Signal(str, float, bool)

    __slots__ = ("gui_args",)

    def __init__(self, args: dict) -> None:
        """Initialize the worker with arguments."""
        super().__init__()
        self.gui_args = args

    def run(self) -> None:
        """Run the Logseq Analyzer application."""
        try:
            start_time = time.perf_counter()
            run_app(**self.gui_args, progress_callback=self.update_progress)
            self.finished_signal.emit("", time.perf_counter() - start_time, True)  # noqa: FBT003
        except KeyboardInterrupt:
            self.finished_signal.emit("Analysis interrupted by user.", 0, False)  # noqa: FBT003
        except Exception as e:
            self.finished_signal.emit(str(e), 0, False)  # noqa: FBT003
            raise

    def update_progress(self, value: int, label: str) -> None:
        """Update the progress bar and label during analysis."""
        self.progress_signal.emit(value)
        self.progress_label.emit(label)
