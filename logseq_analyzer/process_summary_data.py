"""
Process summary data for each file based on metadata and content analysis.
"""

from typing import Any, Dict, List, Set

from ._global_objects import ANALYZER_CONFIG


def check_is_backlinked(name: str, lookup: Set[str]) -> bool:
    """
    Helper function to check if a file is backlinked.
    """
    try:
        lookup.remove(name)
        return True
    except KeyError:
        return False


def determine_file_type(parent: str) -> str:
    """
    Helper function to determine the file type based on the directory structure.
    """
    return {
        ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_ASSETS"): "asset",
        ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_DRAWS"): "draw",
        ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_JOURNALS"): "journal",
        ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_PAGES"): "page",
        ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_WHITEBOARDS"): "whiteboard",
    }.get(parent, "other")


def determine_node_type(has_content: bool, is_backlinked: bool, is_backlinked_ns: bool, has_backlinks: bool) -> str:
    """Helper function to determine node type based on summary data."""
    node_type = "other"
    if has_content:
        if is_backlinked:
            if has_backlinks:
                node_type = "branch"
            else:
                node_type = "leaf"
        elif has_backlinks:
            node_type = "root"
        elif is_backlinked_ns:
            node_type = "orphan_namespace"
        else:
            node_type = "orphan_graph"
    else:  # No content
        if not is_backlinked:
            if is_backlinked_ns:
                node_type = "orphan_namespace_true"
            else:
                node_type = "orphan_true"
        else:
            node_type = "leaf"
    return node_type


def list_files_with_keys(graph_data: Dict[str, Any], *criteria) -> List[str]:
    """
    Extract a subset of the summary data based on whether the keys exists.
    """
    return [k for k, v in graph_data.items() if all(v.get(key) for key in criteria)]


def list_files_without_keys(graph_data: Dict[str, Any], *criteria) -> List[str]:
    """
    Extract a subset of the summary data based on whether the keys do not exist.
    """
    return [k for k, v in graph_data.items() if all(v.get(key) is None for key in criteria)]


def list_files_with_keys_and_values(graph_data: Dict[str, Any], **criteria) -> List[str]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).
    """
    return [k for k, v in graph_data.items() if all(v.get(key) == expected for key, expected in criteria.items())]
