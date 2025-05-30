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

    __slots__ = ("general", "filetypes", "nodetypes", "extensions")

    _SUMMARY_GENERAL = {
        SummaryFiles.BACKLINKED: {"backlinked": True},
        SummaryFiles.BACKLINKED_NS_ONLY: {"backlinked_ns_only": True},
        SummaryFiles.IS_HLS: {"is_hls": True},
        SummaryFiles.HAS_CONTENT: {"has_content": True},
        SummaryFiles.HAS_BACKLINKS: {"has_backlinks": True},
    }

    def __init__(self) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.general: dict[str, list[str]] = defaultdict(list)
        self.filetypes: dict[str, list[str]] = defaultdict(list)
        self.nodetypes: dict[str, list[str]] = defaultdict(list)
        self.extensions: dict[str, list[str]] = defaultdict(list)

    def generate_summary(self, index: "FileIndex") -> None:
        """Generate summary subsets for the Logseq Analyzer."""
        self.get_general_subset(index)
        self.get_filetype_subset(index)
        self.get_nodetype_subset(index)
        self.get_extensions_subset(index)

    def get_general_subset(self, index: "FileIndex") -> None:
        """Generate general subsets for the Logseq Analyzer."""
        result = self.general
        for output_name, file_criteria in self._SUMMARY_GENERAL.items():
            files = index.filter_files(**file_criteria)
            result[output_name.value].extend((file.path.name for file in files))

    def get_filetype_subset(self, index: "FileIndex"):
        """Generate filetype subsets for the Logseq Analyzer."""
        result = self.filetypes
        for file in index:
            result[file.file_type].append(file.path.name)

    def get_nodetype_subset(self, index: "FileIndex"):
        """Generate nodetype subsets for the Logseq Analyzer."""
        result = self.nodetypes
        for file in index:
            result[file.node_type].append(file.path.name)

    def get_extensions_subset(self, index: "FileIndex") -> None:
        """Process file extensions and create subsets for each."""
        result = self.extensions
        for file in index:
            result[file.path.suffix].append(file.path.name)
