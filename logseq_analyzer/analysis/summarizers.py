"""
Logseq Content Summarizer Module
"""

from collections import defaultdict
from enum import StrEnum
from typing import Any

from ..utils.helpers import get_count_and_foundin_data, sort_dict_by_value
from .index import FileIndex

__all__ = [
    "LogseqFileSummarizer",
    "LogseqContentSummarizer",
    "SummaryFile",
]


class SummaryFile(StrEnum):
    """Summary files for the Logseq Analyzer."""

    BACKLINKED = "backlinked"
    BACKLINKED_NS_ONLY = "backlinked_ns_only"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_HLS = "is_hls"


class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    __slots__ = (
        "index",
        "general",
        "filetypes",
        "nodetypes",
        "extensions",
    )

    def __init__(self, index: FileIndex) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.index: FileIndex = index
        self.general: dict[str, list[str]] = defaultdict(list)
        self.filetypes: dict[str, list[str]] = defaultdict(list)
        self.nodetypes: dict[str, list[str]] = defaultdict(list)
        self.extensions: dict[str, list[str]] = defaultdict(list)
        self.process()

    def process(self) -> None:
        """Generate summary subsets for the Logseq Analyzer."""
        self.generate_summary()

    def generate_summary(self) -> None:
        """Generate general subsets for the Logseq Analyzer."""
        for f in self.index:
            f_name = f.path.name
            self.filetypes[f.path.file_type].append(f_name)
            self.nodetypes[f.node.node_type].append(f_name)
            self.extensions[f.path.file.suffix].append(f_name)

            if f.node.backlinked:
                self.general[SummaryFile.BACKLINKED].append(f_name)

            if f.node.backlinked_ns_only:
                self.general[SummaryFile.BACKLINKED_NS_ONLY].append(f_name)

            if f.is_hls:
                self.general[SummaryFile.IS_HLS].append(f_name)

            if f.info.size.has_content:
                self.general[SummaryFile.HAS_CONTENT].append(f_name)

            if f.node.has_backlinks:
                self.general[SummaryFile.HAS_BACKLINKS].append(f_name)

        for k, v in self.general.items():
            self.general[k] = sorted(v)


class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    __slots__ = ("report", "index")

    def __init__(self, index: FileIndex) -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.index: FileIndex = index
        self.report: dict[str, dict[str, Any]] = {}
        self.process()

    def process(self) -> None:
        """Process the Logseq content data."""
        self.generate_summary()
        self.sort_report()

    def generate_summary(self) -> None:
        """Generate summary subsets for content data in the Logseq graph."""
        report = self.report
        for f in self.index:
            if not (f_data := f.data):
                continue

            f_name = f.path.name
            for k, v in f_data.items():
                report.setdefault(k, {})
                report[k] = get_count_and_foundin_data(report[k], v, f_name)

    def sort_report(self) -> None:
        """Sort the report dictionary by count in descending order."""
        report = self.report
        for k in report:
            report[k] = sort_dict_by_value(report[k], value="count", reverse=True)
