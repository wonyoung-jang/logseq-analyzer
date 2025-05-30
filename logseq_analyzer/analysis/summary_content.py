"""
Logseq Content Summarizer Module
"""

from typing import TYPE_CHECKING, Any

from ..utils.enums import Criteria
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

    def generate_summary(self, index: "FileIndex") -> None:
        """Generate summary subsets for content data in the Logseq graph."""
        report = self.report
        for file in index:
            if not file.data:
                continue
            for key, values in file.data.items():
                report.setdefault(key, {})
                report[key] = get_count_and_foundin_data(report[key], values, file)
                report[key] = sort_dict_by_value(report[key], value="count", reverse=True)
        self.check_criteria()

    def check_criteria(self) -> None:
        """Check if all criteria are present in the report."""
        report = self.report
        for criteria in list(Criteria):
            if criteria.value not in report:
                report[criteria.value] = {}
