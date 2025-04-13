"""
Enums for the Logseq Analyzer.
"""

from enum import Enum


class Phase(Enum):
    """Phase of the application."""

    GUI_INSTANCE = "gui_instance"


class Output(Enum):
    """Output types for the Logseq Analyzer."""

    ALL_REFS = "all_refs"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"
    COMPLETE_TIMELINE = "complete_timeline"
    CONFLICTS_DANGLING = "conflicts_dangling"
    CONFLICTS_NON_NAMESPACE = "conflicts_non_namespace"
    CONFLICTS_PARENT_DEPTH = "conflicts_parent_depth"
    CONFLICTS_PARENT_UNIQUE = "conflicts_parent_unique"
    DANGLING_JOURNALS = "dangling_journals"
    DANGLING_JOURNALS_FUTURE = "dangling_journals_future"
    DANGLING_JOURNALS_PAST = "dangling_journals_past"
    DANGLING_LINKS = "dangling_links"
    GRAPH_CONTENT = "__meta__graph_content"
    GRAPH_DATA = "__meta__graph_data"
    GRAPH_HASHED_FILES = "graph_hashed_files"
    GRAPH_MASKED_BLOCKS = "graph_masked_blocks"
    GRAPH_NAMES_TO_HASHES = "graph_names_to_hashes"
    META_UNIQUE_LINKED_REFS = "unique_linked_refs"
    META_UNIQUE_LINKED_REFS_NS = "unique_linked_refs_ns"
    MISSING_KEYS = "missing_keys"
    MOVED_FILES = "moved_files"
    NAMESPACE_DATA = "__meta__namespace_data"
    NAMESPACE_DETAILS = "namespace_details"
    NAMESPACE_HIERARCHY = "namespace_hierarchy"
    NAMESPACE_PARTS = "__meta__namespace_parts"
    NAMESPACE_QUERIES = "namespace_queries"
    PROCESSED_KEYS = "processed_keys"
    TIMELINE_STATS = "timeline_stats"
    UNIQUE_NAMESPACE_PARTS = "unique_namespace_parts"
    UNIQUE_NAMESPACES_PER_LEVEL = "unique_namespaces_per_level"


class SummaryFiles(Enum):
    """Summary files for the Logseq Analyzer."""

    FILE_EXTS = "file_extensions_dict"
    FILETYPE_ASSET = "filetype_asset"
    FILETYPE_DRAW = "filetype_draw"
    FILETYPE_JOURNAL = "filetype_journal"
    FILETYPE_OTHER = "filetype_other"
    FILETYPE_PAGE = "filetype_page"
    FILETYPE_WHITEBOARD = "filetype_whiteboard"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_BACKLINKED = "is_backlinked"
    IS_BACKLINKED_BY_NS_ONLY = "is_backlinked_by_ns_only"
    NODE_BRANCH = "node_branch"
    NODE_LEAF = "node_leaf"
    NODE_ORPHAN_GRAPH = "node_orphan_graph"
    NODE_ORPHAN_NAMESPACE = "node_orphan_namespace"
    NODE_ORPHAN_NAMESPACE_TRUE = "node_orphan_namespace_true"
    NODE_ORPHAN_TRUE = "node_orphan_true"
    NODE_OTHER = "node_other"
    NODE_ROOT = "node_root"
