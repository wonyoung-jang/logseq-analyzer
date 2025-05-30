"""
Logseq File Summarizer Module
"""

from collections import defaultdict
from typing import TYPE_CHECKING

from ..utils.enums import FileTypes, NodeTypes, SummaryFiles
from ..utils.helpers import singleton

if TYPE_CHECKING:
    from .index import FileIndex


@singleton
class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    __slots__ = ("general", "filetypes", "nodetypes")

    _SUMMARY_GENERAL = {
        SummaryFiles.BACKLINKED: {"backlinked": True},
        SummaryFiles.BACKLINKED_NS_ONLY: {"backlinked_ns_only": True},
        SummaryFiles.IS_HLS: {"is_hls": True},
        SummaryFiles.HAS_CONTENT: {"has_content": True},
        SummaryFiles.HAS_BACKLINKS: {"has_backlinks": True},
    }

    _SUMMARY_NODES = {
        NodeTypes.ORPHAN_TRUE: {"node_type": "orphan_true"},
        NodeTypes.ORPHAN_GRAPH: {"node_type": "orphan_graph"},
        NodeTypes.ORPHAN_NAMESPACE: {"node_type": "orphan_namespace"},
        NodeTypes.ORPHAN_NAMESPACE_TRUE: {"node_type": "orphan_namespace_true"},
        NodeTypes.ROOT: {"node_type": "root"},
        NodeTypes.LEAF: {"node_type": "leaf"},
        NodeTypes.BRANCH: {"node_type": "branch"},
        NodeTypes.OTHER: {"node_type": "other"},
    }

    _SUMMARY_FILETYPES = {
        FileTypes.ASSET: {"file_type": "asset"},
        FileTypes.DRAW: {"file_type": "draw"},
        FileTypes.JOURNAL: {"file_type": "journal"},
        FileTypes.PAGE: {"file_type": "page"},
        FileTypes.WHITEBOARD: {"file_type": "whiteboard"},
        FileTypes.SUB_ASSET: {"file_type": "sub_asset"},
        FileTypes.SUB_DRAW: {"file_type": "sub_draw"},
        FileTypes.SUB_JOURNAL: {"file_type": "sub_journal"},
        FileTypes.SUB_PAGE: {"file_type": "sub_page"},
        FileTypes.SUB_WHITEBOARD: {"file_type": "sub_whiteboard"},
        FileTypes.OTHER: {"file_type": "other"},
    }

    def __init__(self) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.general: dict[str, dict[str, list[str]]] = {}
        self.filetypes: dict[str, dict[str, list[str]]] = {}
        self.nodetypes: dict[str, dict[str, list[str]]] = {}

    def generate_summary(self, index: "FileIndex") -> None:
        """Generate summary subsets for the Logseq Analyzer."""
        self.general.update(self.make_subset(index, self._SUMMARY_GENERAL))
        self.filetypes.update(self.make_subset(index, self._SUMMARY_FILETYPES))
        self.nodetypes.update(self.make_subset(index, self._SUMMARY_NODES))
        self.process_file_extensions(index)

    def make_subset(self, index: "FileIndex", mapping: dict[SummaryFiles, dict]) -> dict[str, list[str]]:
        """Generate summary subsets for the Logseq Analyzer."""
        data = {}
        for output_name, file_criteria in mapping.items():
            files = index.filter_files(**file_criteria)
            data[output_name.value] = list((file.path.name for file in files))
        return data

    def process_file_extensions(self, index: "FileIndex") -> None:
        """Process file extensions and create subsets for each."""
        ext_map = defaultdict(list)
        for file in index:
            ext_map[file.path.suffix].append(file.path.name)
        self.general[SummaryFiles.FILE_EXTS.value] = ext_map
