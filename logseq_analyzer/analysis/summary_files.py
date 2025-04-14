"""
Logseq File Summarizer Module
"""

from .graph import LogseqGraph
from ..utils.enums import SummaryFiles


class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LogseqFileSummarizer instance."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.graph = LogseqGraph()
            self.hashed_files = self.graph.hashed_files
            self.subsets = {}

    def generate_summary(self):
        """Generate summary subsets for the Logseq Analyzer."""
        summary_categories = {
            # Process general categories
            SummaryFiles.IS_BACKLINKED: {"is_backlinked": True},
            SummaryFiles.IS_BACKLINKED_BY_NS_ONLY: {"is_backlinked_by_ns_only": True},
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
            self.subsets[output_name.value] = self.list_files_with_keys_and_values(**criteria)

        # Process file extensions
        file_extensions = set()
        for _, file in self.hashed_files.items():
            ext = file.path.suffix
            if ext in file_extensions:
                continue
            file_extensions.add(ext)

        file_ext_dict = {}
        for ext in file_extensions:
            output_name = f"_all_{ext}s"
            criteria = {"suffix": ext}
            file_ext_dict[output_name] = self.list_files_with_keys_and_values(**criteria)
        self.subsets[SummaryFiles.FILE_EXTS.value] = file_ext_dict

    def list_files_with_keys_and_values(self, **criteria) -> list:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for _, file in self.hashed_files.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.path.name)
        return result
