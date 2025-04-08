"""
Process summary data for each file based on metadata and content analysis.
"""

from typing import Any, Dict, Generator, List, Set

from .logseq_file import LogseqFile


def check_is_backlinked(name: str, lookup: Set[str]) -> bool:
    """
    Helper function to check if a file is backlinked.
    """
    try:
        lookup.remove(name)
        return True
    except KeyError:
        return False


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


def yield_files_with_keys(files: List[LogseqFile], *criteria) -> Generator[str, None, None]:
    """
    Extract a subset of the summary data based on whether the keys exists.
    """
    for file in files:
        if all(hasattr(file, key) for key in criteria):
            yield file


def yield_files_without_keys(graph_data: Dict[str, Any], *criteria) -> Generator[str, None, None]:
    """
    Extract a subset of the summary data based on whether the keys do not exist.
    """
    for k, v in graph_data.items():
        if all(v.get(key) is None for key in criteria):
            yield k


def yield_files_with_keys_and_values(graph_data: Dict[str, Any], **criteria) -> Generator[str, None, None]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).
    """
    for k, v in graph_data.items():
        if all(v.get(key) == expected for key, expected in criteria.items()):
            yield k


def list_files_with_keys(graph_data: Dict[str, Any], *criteria) -> List[str]:
    """
    Extract a subset of the summary data based on whether the keys exists.
    """
    return [k for k, v in graph_data.items() if all(v.get(key) for key in criteria)]


def list_files_without_keys(files: List[LogseqFile], *criteria) -> List[str]:
    """
    Extract a subset of the summary data based on whether the keys do not exist.
    """
    return [file.name for file in files if all(not hasattr(file, key) for key in criteria)]


def list_files_with_keys_and_values(graph_data: Dict[str, Any], **criteria) -> List[str]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).
    """
    return [k for k, v in graph_data.items() if all(v.get(key) == expected for key, expected in criteria.items())]
