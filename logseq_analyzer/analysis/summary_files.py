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
        self.general: dict[str, list[str]] = defaultdict(list)
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
        self.general[SummaryFiles.BACKLINKED.value] = sorted(
            file.filename.name for file in index if file.node.backlinked
        )
        self.general[SummaryFiles.BACKLINKED_NS_ONLY.value] = sorted(
            file.filename.name for file in index if file.node.backlinked_ns_only
        )
        self.general[SummaryFiles.IS_HLS.value] = sorted(file.filename.name for file in index if file.filename.is_hls)
        self.general[SummaryFiles.HAS_CONTENT.value] = sorted(
            file.filename.name for file in index if file.stat.has_content
        )
        self.general[SummaryFiles.HAS_BACKLINKS.value] = sorted(
            file.filename.name for file in index if file.node.has_backlinks
        )

    def get_filetype_subset(self, index: "FileIndex"):
        """Generate filetype subsets for the Logseq Analyzer."""
        for file in index:
            self.filetypes[file.filename.file_type].append(file.filename.name)

    def get_nodetype_subset(self, index: "FileIndex"):
        """Generate nodetype subsets for the Logseq Analyzer."""
        for file in index:
            self.nodetypes[file.node.type].append(file.filename.name)

    def get_extensions_subset(self, index: "FileIndex") -> None:
        """Process file extensions and create subsets for each."""
        for file in index:
            self.extensions[file.path.suffix].append(file.filename.name)
