"""
Logseq File Summarizer Module
"""

from typing import Dict

from .index import FileIndex

from ..utils.enums import SummaryFiles
from ..utils.helpers import singleton
from .query_graph import Query


@singleton
class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    def __init__(self):
        """Initialize the LogseqFileSummarizer instance."""
        self.subsets: Dict[str, dict] = {}

    def generate_summary(self):
        """Generate summary subsets for the Logseq Analyzer."""
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
        for output_name, criteria in summary_categories.items():
            self.subsets[output_name.value] = Query().list_file_names_with_keys_and_values(**criteria)

        self.process_file_extensions()

    def process_file_extensions(self):
        """Process file extensions and create subsets for each."""
        file_extension_dict = {}
        for file in FileIndex().files:
            ext = file.path.suffix
            output_name = f"all {ext}s"
            if output_name not in file_extension_dict:
                criteria = {"suffix": ext}
                file_extension_dict[output_name] = Query().list_file_names_with_keys_and_values(**criteria)
        self.subsets[SummaryFiles.FILE_EXTS.value] = file_extension_dict
