"""
Logseq Content Summarizer Module
"""

from typing import Any, Dict

from ..utils.enums import Criteria
from ..utils.helpers import singleton, sort_dict_by_value
from .index import FileIndex


@singleton
class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    def __init__(self):
        """Initialize the LogseqContentSummarizer instance."""
        self.subsets = {}

    def __repr__(self):
        """Return a string representation of the LogseqContentSummarizer instance."""
        return "LogseqContentSummarizer()"

    def __str__(self):
        """Return a string representation of the LogseqContentSummarizer instance."""
        return "LogseqContentSummarizer"

    def __len__(self):
        """Return the number of subsets."""
        return len(self.subsets)

    def generate_summary(self):
        """Generate summary subsets for content data in the Logseq graph."""
        for criteria in list(Criteria):
            self.subsets[criteria.value] = self.extract_summary_subset_content(criteria.value)

    def extract_summary_subset_content(self, criteria) -> Dict[str, Any]:
        """
        Extract a subset of data based on a specific criteria.
        Asks: What content matches the criteria? And where is it found? How many times?

        Args:
            criteria (str): The criteria for extraction.

        Returns:
            Dict[str, Any]: A dictionary containing the count and locations of the extracted values.
        """
        subset_counter = {}
        index = FileIndex()
        for file in index.files:
            for value in file.data.get(criteria, []):
                subset_counter.setdefault(value, {})
                subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                subset_counter[value].setdefault("found_in", []).append(file.path.name)
        return sort_dict_by_value(subset_counter, value="count", reverse=True)
