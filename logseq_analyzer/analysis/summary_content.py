"""
Logseq Content Summarizer Module
"""

from typing import TYPE_CHECKING, Any

from ..utils.helpers import get_count_and_foundin_data, singleton, sort_dict_by_value

if TYPE_CHECKING:
    from .index import FileIndex


@singleton
class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    __slots__ = ("report",)

    def __init__(self) -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.report: dict[str, dict[str, Any]] = {}

    def process(self, index: "FileIndex") -> None:
        """Process the Logseq content data."""
        self.generate_summary(index)
        self.sort_report()

    def generate_summary(self, index: "FileIndex") -> None:
        """Generate summary subsets for content data in the Logseq graph."""
        for f in index:
            for key, values in f.data.items():
                self.report.setdefault(key, {})
                self.report[key] = get_count_and_foundin_data(self.report[key], values, f)

    def sort_report(self) -> None:
        """Sort the report dictionary by count in descending order."""
        for key in self.report:
            self.report[key] = sort_dict_by_value(self.report[key], value="count", reverse=True)
