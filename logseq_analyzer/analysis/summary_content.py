"""
Logseq Content Summarizer Module
"""

from collections import Counter
from typing import Any, TYPE_CHECKING

from ..utils.enums import Criteria
from ..utils.helpers import singleton, sort_dict_by_value

if TYPE_CHECKING:
    from .index import FileIndex


@singleton
class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    __slots__ = ("report", "index")

    def __init__(self, index: "FileIndex") -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.report: dict[str, dict[str, Any]] = {}
        self.index = index

    def generate_summary(self) -> None:
        """Generate summary subsets for content data in the Logseq graph."""
        report = self.report
        for criteria in list(Criteria):
            criteria_value = criteria.value
            report[criteria_value] = self.extract_content(criteria_value)

    def extract_content(self, criteria: str) -> dict[str, Any]:
        """
        Extract a subset of data based on a specific criteria.
        Asks: What content matches the criteria? And where is it found? How many times?

        Args:
            criteria (str): The criteria for extraction.

        Returns:
            dict[str, Any]: A dictionary containing the count and locations of the extracted values.
        """
        index = self.index
        subset_counter = {}
        for file in index:
            for value in file.data.get(criteria, []):
                subset_counter.setdefault(value, {"count": 0, "found_in": Counter()})
                subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                subset_counter[value]["found_in"][file.path.name] += 1
        return sort_dict_by_value(subset_counter, value="count", reverse=True)
