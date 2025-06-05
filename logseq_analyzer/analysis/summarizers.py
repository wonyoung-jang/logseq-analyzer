"""
Logseq Content Summarizer Module
"""

from collections import defaultdict
from typing import Any

from ..utils.enums import SummaryFiles
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
        self.general: dict[str, list[str]] = {}
        self.filetypes: dict[str, list[str]] = defaultdict(list)
        self.nodetypes: dict[str, list[str]] = defaultdict(list)
        self.extensions: dict[str, list[str]] = defaultdict(list)
        self.process()

    def process(self) -> None:
        """Generate summary subsets for the Logseq Analyzer."""
        self.get_general_subset()
        self.get_filetype_subset()
        self.get_nodetype_subset()
        self.get_extensions_subset()

    def get_general_subset(self) -> None:
        """Generate general subsets for the Logseq Analyzer."""
        index = self.index
        g = self.general
        g[SummaryFiles.BACKLINKED.value] = sorted(f.path.name for f in index if f.node.backlinked)
        g[SummaryFiles.BACKLINKED_NS_ONLY.value] = sorted(f.path.name for f in index if f.node.backlinked_ns_only)
        g[SummaryFiles.IS_HLS.value] = sorted(f.path.name for f in index if f.is_hls)
        g[SummaryFiles.HAS_CONTENT.value] = sorted(f.path.name for f in index if f.info.size.has_content)
        g[SummaryFiles.HAS_BACKLINKS.value] = sorted(f.path.name for f in index if f.node.has_backlinks)

    def get_filetype_subset(self) -> None:
        """Generate filetype subsets for the Logseq Analyzer."""
        filetypes = self.filetypes
        for f in self.index:
            filetypes[f.path.file_type].append(f.path.name)

    def get_nodetype_subset(self):
        """Generate nodetype subsets for the Logseq Analyzer."""
        nodetypes = self.nodetypes
        for f in self.index:
            nodetypes[f.node.node_type].append(f.path.name)

    def get_extensions_subset(self) -> None:
        """Process file extensions and create subsets for each."""
        extensions = self.extensions
        for f in self.index:
            extensions[f.path.file.suffix].append(f.path.name)


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
