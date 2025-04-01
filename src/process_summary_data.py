"""
Process summary data for each file based on metadata and content analysis.
"""

from typing import Any, Dict, List, Set

from ._global_objects import ANALYZER_CONFIG


HAS_BACKLINKS = [
    "page_references",
    "tags",
    "tagged_backlinks",
    "properties_page_builtin",
    "properties_page_user",
    "properties_block_builtin",
    "properties_block_user",
]


def has_key_with_values(data, *keys) -> bool:
    """
    Generalized helper function to check if any of the specified keys in the data have values.
    """
    return any(data.get(key) for key in keys)


def check_has_backlinks(data) -> bool:
    """
    Helper function to check if a file has backlinks.
    """
    return any(data.get(key) for key in HAS_BACKLINKS)


def check_is_backlinked(
    name: str, graph_data: Dict[str, Any], alphanum_dict: Dict[str, Set[str]], is_backlinked_not_ns: bool = False
) -> bool:
    """
    Helper function to check if a file is backlinked.
    """
    if is_backlinked_not_ns:
        return False

    id_key = graph_data["id"]
    if id_key in alphanum_dict:
        if name in alphanum_dict[id_key]:
            return True
    return False


def determine_file_type(file_path_parent_name: str, file_path_parts: List[str]) -> str:
    """
    Helper function to determine the file type based on the directory structure.
    """
    assets_dir = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_ASSETS")
    draws_dir = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_DRAWS")
    journals_dir = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_JOURNALS")
    pages_dir = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_PAGES")
    whiteboards_dir = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_WHITEBOARDS")

    file_type = None

    if file_path_parent_name == assets_dir or assets_dir in file_path_parts:
        file_type = "asset"
    elif file_path_parent_name == draws_dir:
        file_type = "draw"
    elif file_path_parent_name == journals_dir:
        file_type = "journal"
    elif file_path_parent_name == pages_dir:
        file_type = "page"
    elif file_path_parent_name == whiteboards_dir:
        file_type = "whiteboard"
    else:
        file_type = "other"

    return file_type


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


def get_data_with_keys(graph_data: Dict[str, Any], *criteria) -> Dict[str, Any]:
    """
    Extract a subset of the summary data based on whether the keys exists.
    """
    return {k: v for k, v in graph_data.items() if all(v.get(key) for key in criteria)}


def get_data_with_keys_and_values(graph_data: Dict[str, Any], **criteria) -> Dict[str, Any]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).
    """
    return {k: v for k, v in graph_data.items() if all(v.get(key) == expected for key, expected in criteria.items())}


def generate_sorted_summary_all(graph_data: Dict[str, Any], count: int = 0, reverse: bool = True) -> Dict[str, Any]:
    """
    Generate a sorted summary for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data to analyze.
    """
    flipped_data = {}
    for name, data in graph_data.items():
        for key, value in data.items():
            key = f"_pages_with_{key}"
            if value:
                if isinstance(value, (list, dict, set, tuple)):
                    flipped_data.setdefault(key, {})[name] = len(value)
                else:
                    flipped_data.setdefault(key, {})[name] = value

    for key, value in flipped_data.items():
        sorted_data = dict(sorted(value.items(), key=lambda item: item[1], reverse=reverse))
        value = sorted_data
        if count > 0:
            value = dict(sorted_data.items()[:count])

    return flipped_data
