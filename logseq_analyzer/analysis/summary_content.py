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

    __slots__ = ("subsets",)

    def __init__(self) -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.subsets = {}

    def generate_summary(self, index: "FileIndex") -> None:
        """Generate summary subsets for content data in the Logseq graph."""
        subsets = self.subsets
        for criteria in list(Criteria):
            criteria_value = criteria.value
            subsets[criteria_value] = self.extract_summary_subset_content(criteria_value, index)

    @staticmethod
    def extract_summary_subset_content(criteria: str, index: "FileIndex") -> dict[str, Any]:
        """
        Extract a subset of data based on a specific criteria.
        Asks: What content matches the criteria? And where is it found? How many times?

        Args:
            criteria (str): The criteria for extraction.
            index (FileIndex): The file index to search through.

        Returns:
            dict[str, Any]: A dictionary containing the count and locations of the extracted values.
        """
        subset_counter = {}
        for file in index:
            for value in file.data.get(criteria, []):
                subset_counter.setdefault(value, {"count": 0, "found_in": Counter()})
                subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                subset_counter[value]["found_in"][file.path.name] += 1
        return sort_dict_by_value(subset_counter, value="count", reverse=True)
