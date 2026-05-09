"""Worker thread for running the Logseq Analyzer application."""

from time import perf_counter

from PySide6.QtCore import QThread, Signal

from logseq_analyzer.app import run_app


# ruff: noqa: FBT003
class AnalysisWorker(QThread):
    """Thread worker for running the Logseq Analyzer application."""

    progress_signal = Signal(int)
    progress_label = Signal(str)
    finished_signal = Signal(str, float, bool)

    def __init__(self, args: dict) -> None:
        """Initialize the worker with arguments."""
        super().__init__()
        self.gui_args = args

    def run(self) -> None:
        """Run the Logseq Analyzer application."""
        try:
            _start = perf_counter()
            self.gui_args["progress_callback"] = self.update_progress
            run_app(arguments=self.gui_args)
            self.finished_signal.emit("", perf_counter() - _start, True)
        except KeyboardInterrupt:
            self.finished_signal.emit("Analysis interrupted by user.", 0, False)
        except Exception as e:
            self.finished_signal.emit(str(e), 0, False)
            raise

    def update_progress(self, value: int, label: str) -> None:
        """Update the progress bar and label during analysis."""
        self.progress_signal.emit(value)
        self.progress_label.emit(label)
