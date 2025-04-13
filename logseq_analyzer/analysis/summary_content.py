"""
Logseq Content Summarizer Module
"""

from typing import Any, Dict
from .graph import LogseqGraph


class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LogseqContentSummarizer instance."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.graph = LogseqGraph()
            self.hashed_files = self.graph.hashed_files
            self.subsets = {}

    def generate_summary(self):
        """Generate summary subsets for content data in the Logseq graph."""
        content_subset_tags_nodes = [
            "advanced_commands_caution",
            "advanced_commands_center",
            "advanced_commands_comment",
            "advanced_commands_example",
            "advanced_commands_export_ascii",
            "advanced_commands_export_latex",
            "advanced_commands_export",
            "advanced_commands_important",
            "advanced_commands_note",
            "advanced_commands_pinned",
            "advanced_commands_query",
            "advanced_commands_quote",
            "advanced_commands_tip",
            "advanced_commands_verse",
            "advanced_commands_warning",
            "advanced_commands",
            "aliases",
            "any_links",
            "assets",
            "block_embeds",
            "block_references",
            "blockquotes",
            "calc_blocks",
            "cards",
            "clozes",
            "draws",
            "dynamic_variables",
            "embed_twitter_tweets",
            "embed_video_urls",
            "embed_youtube_timestamps",
            "embedded_links_asset",
            "embedded_links_internet",
            "embedded_links_other",
            "embeds",
            "external_links_alias",
            "external_links_internet",
            "external_links_other",
            "flashcards",
            "inline_code_blocks",
            "macros",
            "multiline_code_blocks",
            "multiline_code_langs",
            "namespace_queries",
            "page_embeds",
            "page_references",
            "properties_block_builtin",
            "properties_block_user",
            "properties_page_builtin",
            "properties_page_user",
            "properties_values",
            "query_functions",
            "references_general",
            "renderers",
            "simple_queries",
            "tagged_backlinks",
            "tags",
        ]
        for criteria in content_subset_tags_nodes:
            self.subsets[f"content_{criteria}"] = self.extract_summary_subset_content(criteria)

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
        for _, file in self.hashed_files.items():
            if file.data.get(criteria):
                for value in file.data[criteria]:
                    subset_counter.setdefault(value, {})
                    subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                    subset_counter[value].setdefault("found_in", []).append(file.path.name)
        return dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))
