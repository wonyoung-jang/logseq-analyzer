"""
Logseq Content Summarizer Module
"""

from collections import defaultdict
from typing import Any

from ..utils.enums import SummaryFile
from ..utils.helpers import get_count_and_foundin_data, sort_dict_by_value
from .index import FileIndex

__all__ = [
    "LogseqFileSummarizer",
    "LogseqContentSummarizer",
]


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
        SF = SummaryFile
        gen = self.general
        for f in self.index:
            name = f.path.name
            self.filetypes[f.path.file_type].append(name)
            self.nodetypes[f.node.node_type].append(name)
            self.extensions[f.path.file.suffix].append(name)

            if f.node.backlinked:
                gen[SF.BACKLINKED.value].append(name)

            if f.node.backlinked_ns_only:
                gen[SF.BACKLINKED_NS_ONLY.value].append(name)

            if f.is_hls:
                gen[SF.IS_HLS.value].append(name)

            if f.info.size.has_content:
                gen[SF.HAS_CONTENT.value].append(name)

            if f.node.has_backlinks:
                gen[SF.HAS_BACKLINKS.value].append(name)

        for k, v in gen.items():
            gen[k] = sorted(v)


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
            for k, v in f.data.items():
                report.setdefault(k, {})
                report[k] = get_count_and_foundin_data(report[k], v, f.path.name)

    def sort_report(self) -> None:
        """Sort the report dictionary by count in descending order."""
        report = self.report
        for k in report:
            report[k] = sort_dict_by_value(report[k], value="count", reverse=True)
