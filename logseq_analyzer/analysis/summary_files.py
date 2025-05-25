"""
Logseq File Summarizer Module
"""

from collections import defaultdict
from typing import TYPE_CHECKING

from ..utils.enums import SummaryFiles
from ..utils.helpers import singleton
from .index import get_attribute_list

if TYPE_CHECKING:
    from .index import FileIndex


@singleton
class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    __slots__ = ("subsets",)

    summary_categories = {
        # Process general categories
        SummaryFiles.IS_BACKLINKED: {"is_backlinked": True},
        SummaryFiles.IS_BACKLINKED_BY_NS_ONLY: {"is_backlinked_by_ns_only": True},
        SummaryFiles.IS_HLS: {"is_hls": True},
        SummaryFiles.HAS_CONTENT: {"has_content": True},
        SummaryFiles.HAS_BACKLINKS: {"has_backlinks": True},
        # Process file types
        SummaryFiles.FILETYPE_ASSET: {"file_type": "asset"},
        SummaryFiles.FILETYPE_DRAW: {"file_type": "draw"},
        SummaryFiles.FILETYPE_JOURNAL: {"file_type": "journal"},
        SummaryFiles.FILETYPE_PAGE: {"file_type": "page"},
        SummaryFiles.FILETYPE_WHITEBOARD: {"file_type": "whiteboard"},
        SummaryFiles.FILETYPE_SUB_ASSET: {"file_type": "sub_asset"},
        SummaryFiles.FILETYPE_SUB_DRAW: {"file_type": "sub_draw"},
        SummaryFiles.FILETYPE_SUB_JOURNAL: {"file_type": "sub_journal"},
        SummaryFiles.FILETYPE_SUB_PAGE: {"file_type": "sub_page"},
        SummaryFiles.FILETYPE_SUB_WHITEBOARD: {"file_type": "sub_whiteboard"},
        SummaryFiles.FILETYPE_OTHER: {"file_type": "other"},
        # Process nodes
        SummaryFiles.NODE_ORPHAN_TRUE: {"node_type": "orphan_true"},
        SummaryFiles.NODE_ORPHAN_GRAPH: {"node_type": "orphan_graph"},
        SummaryFiles.NODE_ORPHAN_NAMESPACE: {"node_type": "orphan_namespace"},
        SummaryFiles.NODE_ORPHAN_NAMESPACE_TRUE: {"node_type": "orphan_namespace_true"},
        SummaryFiles.NODE_ROOT: {"node_type": "root"},
        SummaryFiles.NODE_LEAF: {"node_type": "leaf"},
        SummaryFiles.NODE_BRANCH: {"node_type": "branch"},
        SummaryFiles.NODE_OTHER: {"node_type": "other"},
    }

    def __init__(self) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.subsets: dict[str, dict[str, list[str]]] = {}

    def generate_summary(self, index: "FileIndex") -> None:
        """Generate summary subsets for the Logseq Analyzer."""
        summary_categories = self.summary_categories
        subsets = self.subsets
        for output_name, file_criteria in summary_categories.items():
            files = index.filter_files(**file_criteria)
            subsets[output_name.value] = get_attribute_list(files, "name")
        self.process_file_extensions(index)

    def process_file_extensions(self, index: "FileIndex") -> None:
        """Process file extensions and create subsets for each."""
        ext_map = defaultdict(list)
        for file in index:
            if suffix := file.path.suffix:
                name = f"all {suffix}s"
                ext_map[name].append(file.path.name)
        self.subsets[SummaryFiles.FILE_EXTS.value] = ext_map
