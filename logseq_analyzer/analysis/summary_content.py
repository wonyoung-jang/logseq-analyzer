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
        for criteria in list(Criteria):
            criteria_value = criteria.value
            report[criteria_value] = self.extract_content(index, criteria_value)

    def extract_content(self, index: "FileIndex", criteria: str) -> dict[str, Any]:
        """
        Extract a subset of data based on a specific criteria.
        Asks: What content matches the criteria? And where is it found? How many times?

        Args:
            criteria (str): The criteria for extraction.

        Returns:
            dict[str, Any]: A dictionary containing the count and locations of the extracted values.
        """
        subset_counter = {}
        for file in index:
            if not (file_criteria := file.data.get(criteria, [])):
                continue
            get_count_and_foundin_data(subset_counter, file_criteria, file)
        return sort_dict_by_value(subset_counter, value="count", reverse=True)
