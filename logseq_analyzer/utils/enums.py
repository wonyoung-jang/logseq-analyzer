"""
Enums for the Logseq Analyzer.
"""

from enum import Enum


class Phase(Enum):
    """Phase of the application."""

    GUI_INSTANCE = "gui_instance"


class Output(Enum):
    """Output types for the Logseq Analyzer."""

    DANGLING_JOURNALS = "dangling_journals"
    PROCESSED_KEYS = "processed_keys"
    COMPLETE_TIMELINE = "complete_timeline"
    MISSING_KEYS = "missing_keys"
    TIMELINE_STATS = "timeline_stats"
    DANGLING_JOURNALS_PAST = "dangling_journals_past"
    DANGLING_JOURNALS_FUTURE = "dangling_journals_future"
    META_UNIQUE_LINKED_REFS = "___meta___unique_linked_refs"
    META_UNIQUE_LINKED_REFS_NS = "___meta___unique_linked_refs_ns"
    GRAPH_DATA = "___meta___graph_data"
    GRAPH_CONTENT = "___meta___graph_content"
    ALL_REFS = "all_refs"
    DANGLING_LINKS = "dangling_links"
    GRAPH_HASHED_FILES = "graph_hashed_files"
    GRAPH_NAMES_TO_HASHES = "graph_names_to_hashes"
    GRAPH_MASKED_BLOCKS = "graph_masked_blocks"
    NAMESPACE_DATA = "___meta___namespace_data"
    NAMESPACE_PARTS = "___meta___namespace_parts"
    UNIQUE_NAMESPACE_PARTS = "unique_namespace_parts"
    NAMESPACE_DETAILS = "namespace_details"
    UNIQUE_NAMESPACES_PER_LEVEL = "unique_namespaces_per_level"
    NAMESPACE_QUERIES = "namespace_queries"
    NAMESPACE_HIERARCHY = "namespace_hierarchy"
    CONFLICTS_NON_NAMESPACE = "conflicts_non_namespace"
    CONFLICTS_DANGLING = "conflicts_dangling"
    CONFLICTS_PARENT_DEPTH = "conflicts_parent_depth"
    CONFLICTS_PARENT_UNIQUE = "conflicts_parent_unique"
    MOVED_FILES = "moved_files"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"
