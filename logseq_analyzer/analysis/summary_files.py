"""
Logseq File Summarizer Module
"""

from collections import defaultdict
from typing import TYPE_CHECKING

from ..utils.enums import SummaryFiles
from ..utils.helpers import singleton

if TYPE_CHECKING:
    from .index import FileIndex


@singleton
class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    __slots__ = (
        "general",
        "filetypes",
        "nodetypes",
        "extensions",
    )

    def __init__(self) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.general: dict[str, list[str]] = {}
        self.filetypes: dict[str, list[str]] = defaultdict(list)
        self.nodetypes: dict[str, list[str]] = defaultdict(list)
        self.extensions: dict[str, list[str]] = defaultdict(list)

    def process(self, index: "FileIndex") -> None:
        """Generate summary subsets for the Logseq Analyzer."""
        self.get_general_subset(index)
        self.get_filetype_subset(index)
        self.get_nodetype_subset(index)
        self.get_extensions_subset(index)

    def get_general_subset(self, index: "FileIndex") -> None:
        """Generate general subsets for the Logseq Analyzer."""
        g = self.general
        g[SummaryFiles.BACKLINKED.value] = sorted(f.name for f in index if f.backlinked)
        g[SummaryFiles.BACKLINKED_NS_ONLY.value] = sorted(f.name for f in index if f.backlinked_ns_only)
        g[SummaryFiles.IS_HLS.value] = sorted(f.name for f in index if f.is_hls)
        g[SummaryFiles.HAS_CONTENT.value] = sorted(f.name for f in index if f.has_content)
        g[SummaryFiles.HAS_BACKLINKS.value] = sorted(f.name for f in index if f.has_backlinks)

    def get_filetype_subset(self, index: "FileIndex"):
        """Generate filetype subsets for the Logseq Analyzer."""
        for f in index:
            self.filetypes[f.file_type].append(f.name)

    def get_nodetype_subset(self, index: "FileIndex"):
        """Generate nodetype subsets for the Logseq Analyzer."""
        for f in index:
            self.nodetypes[f.node_type].append(f.name)

    def get_extensions_subset(self, index: "FileIndex") -> None:
        """Process file extensions and create subsets for each."""
        for f in index:
            self.extensions[f.suffix].append(f.name)
