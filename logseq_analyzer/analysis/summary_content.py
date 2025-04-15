"""
Logseq Content Summarizer Module
"""

from typing import Any, Dict

from ..utils.helpers import singleton
from .graph import LogseqGraph
from ..utils.enums import Criteria


@singleton
class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    def __init__(self):
        """Initialize the LogseqContentSummarizer instance."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.graph = LogseqGraph()
            self.subsets = {}

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
        for _, file in self.graph.hash_to_file_map.items():
            for value in file.data.get(criteria, []):
                subset_counter.setdefault(value, {})
                subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                subset_counter[value].setdefault("found_in", []).append(file.path.name)
        return dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))
