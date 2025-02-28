import src.config as config
from typing import Any, Dict, Set
from collections import defaultdict


def process_summary_data(
    graph_meta_data: Dict[str, Any],
    graph_content_data: Dict[str, Any],
    alphanum_dict: Dict[str, Set[str]],
) -> Dict[str, Any]:
    """
    Process summary data for each file based on metadata and content analysis.

    Categorizes files and determines node types (root, leaf, branch, orphan).

    Args:
        graph_meta_data (Dict[str, Any]): Metadata for each file.
        graph_content_data (Dict[str, Any]): Content-based data for each file.
        alphanum_dict (Dict[str, Set[str]]): Dictionary for quick lookup of linked references.

    Returns:
        Dict[str, Any]: Summary data for each file.
    """
    graph_summary_data = defaultdict(lambda: defaultdict(bool))

    assets_dir = config.ASSETS
    draws_dir = config.DRAWS
    journals_dir = config.JOURNALS
    pages_dir = config.PAGES
    whiteboards_dir = config.WHITEBOARDS

    for name, meta_data in graph_meta_data.items():
        content_info = graph_content_data.get(name, {})
        has_content = bool(content_info)
        has_backlinks = False
        has_external_links = False
        has_embedded_links = False
        if has_content:
            has_backlinks = any(
                content_info.get(key)
                for key in [
                    "page_references",
                    "tags",
                    "tagged_backlinks",
                    "properties_page_builtin",
                    "properties_page_user",
                    "properties_block_builtin",
                    "properties_block_user",
                ]
            )
            has_external_links = any(
                content_info.get(key)
                for key in [
                    "external_links",
                    "external_links_internet",
                    "external_links_alias",
                ]
            )
            has_embedded_links = any(
                content_info.get(key)
                for key in [
                    "embedded_links",
                    "embedded_links_internet",
                    "embedded_links_asset",
                ]
            )

        file_extension = meta_data["file_path_suffix"]
        file_path_parent_name = meta_data["file_path_parent_name"]
        file_path_parts = meta_data["file_path_parts"]

        if file_path_parent_name == assets_dir or assets_dir in file_path_parts:
            file_type = config.FILE_TYPE_ASSET
        elif file_path_parent_name == draws_dir:
            file_type = config.FILE_TYPE_DRAW
        elif file_path_parent_name == journals_dir:
            file_type = config.FILE_TYPE_JOURNAL
        elif file_path_parent_name == pages_dir:
            file_type = config.FILE_TYPE_PAGE
        elif file_path_parent_name == whiteboards_dir:
            file_type = config.FILE_TYPE_WHITEBOARD
        else:
            file_type = config.FILE_TYPE_OTHER

        is_backlinked = check_is_backlinked(name, meta_data, alphanum_dict)
        node_type = config.NODE_TYPE_OTHER
        if file_type in [config.FILE_TYPE_JOURNAL, config.FILE_TYPE_PAGE]:
            node_type = determine_node_type(has_content, is_backlinked, has_backlinks)

        graph_summary_data[name]["file_type"] = file_type
        graph_summary_data[name]["file_extension"] = file_extension
        graph_summary_data[name]["node_type"] = node_type
        graph_summary_data[name]["has_content"] = has_content
        graph_summary_data[name]["has_backlinks"] = has_backlinks
        graph_summary_data[name]["has_external_links"] = has_external_links
        graph_summary_data[name]["has_embedded_links"] = has_embedded_links
        graph_summary_data[name]["is_backlinked"] = is_backlinked

    return graph_summary_data


def check_is_backlinked(name: str, meta_data: Dict[str, Any], alphanum_dict: Dict[str, Set[str]]) -> bool:
    """
    Helper function to check if a file is backlinked.

    Args:
        name (str): The file name.
        meta_data (Dict[str, Any]): Metadata for the file.
        alphanum_dict (Dict[str, Set[str]]): Dictionary for quick lookup of linked references.

    Returns:
        bool: True if the file is backlinked; otherwise, False.
    """
    id_key = meta_data["id"]
    if id_key in alphanum_dict:
        for page_ref in alphanum_dict[id_key]:
            if name == page_ref or str(name + config.NAMESPACE_SEP) in page_ref:
                return True
    return False


def determine_node_type(has_content: bool, is_backlinked: bool, has_backlinks: bool) -> str:
    """Helper function to determine node type based on summary data."""
    if has_content:
        if is_backlinked:
            if has_backlinks:
                return config.NODE_TYPE_BRANCH
            else:
                return config.NODE_TYPE_LEAF
        else:
            if has_backlinks:
                return config.NODE_TYPE_ROOT
            else:
                return config.NODE_TYPE_ORPHAN_GRAPH
    else:
        if not is_backlinked:
            return config.NODE_TYPE_ORPHAN_TRUE
        else:
            return config.NODE_TYPE_LEAF


def extract_summary_subset(graph_summary_data: Dict[str, Any], **criteria: Any) -> Dict[str, Any]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).

    Args:
        graph_summary_data (Dict[str, Any]): The complete summary data.
        **criteria: Keyword arguments specifying the criteria for subset extraction.

    Returns:
        Dict[str, Any]: A subset of the summary data matching the criteria.
    """
    return {k: v for k, v in graph_summary_data.items() if all(v.get(key) == expected for key, expected in criteria.items())}
