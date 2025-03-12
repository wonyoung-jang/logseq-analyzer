import src.config as config
from typing import Any, Dict, List, Set


def init_summary_data() -> Dict[str, Any]:
    """
    Initialize an empty summary data dictionary.

    Returns:
        Dict[str, Any]: An empty dictionary for summary data.
    """
    return {
        "file_type": "",
        "file_extension": "",
        "node_type": "",
        "has_content": False,
        "has_backlinks": False,
        "has_external_links": False,
        "has_embedded_links": False,
        "is_backlinked": False,
    }


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
    graph_summary_data = {}

    assets_dir = config.DIR_ASSETS
    draws_dir = config.DIR_DRAWS
    journals_dir = config.DIR_JOURNALS
    pages_dir = config.DIR_PAGES
    whiteboards_dir = config.DIR_WHITEBOARDS

    for name, meta_data in graph_meta_data.items():
        graph_summary_data[name] = init_summary_data()
        content_info = graph_content_data.get(name, {})
        has_content = bool(meta_data["size"] > 0)
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
        file_path_parent_name = meta_data["file_path_parent_name"]
        file_path_parts = meta_data["file_path_parts"]

        file_type = determine_file_type(
            assets_dir, draws_dir, journals_dir, pages_dir, whiteboards_dir, file_path_parent_name, file_path_parts
        )
        is_backlinked = check_is_backlinked(name, meta_data, alphanum_dict)
        node_type = config.NODE_TYPE_OTHER
        if file_type in [config.FILE_TYPE_JOURNAL, config.FILE_TYPE_PAGE]:
            node_type = determine_node_type(has_content, is_backlinked, has_backlinks)

        graph_summary_data[name]["file_type"] = file_type
        graph_summary_data[name]["file_extension"] = meta_data["file_path_suffix"]
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


def determine_file_type(
    assets_dir: str,
    draws_dir: str,
    journals_dir: str,
    pages_dir: str,
    whiteboards_dir: str,
    file_path_parent_name: str,
    file_path_parts: List[str],
) -> str:
    """
    Helper function to determine the file type based on the directory structure.

    Args:
        assets_dir (str): Directory for assets.
        draws_dir (str): Directory for draws.
        journals_dir (str): Directory for journals.
        pages_dir (str): Directory for pages.
        whiteboards_dir (str): Directory for whiteboards.
        file_path_parent_name (str): The parent name of the file path.
        file_path_parts (List[str]): Parts of the file path.

    Returns:
        str: The determined file type.
    """
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
    return file_type


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


def extract_summary_subset(graph_summary_data: Dict[str, Any], **criteria) -> List[str]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).

    Args:
        graph_summary_data (Dict[str, Any]): The complete summary data.
        **criteria: Keyword arguments specifying the criteria for subset extraction.

    Returns:
        List[str]: A list of keys from the summary data that match the criteria.
    """
    summary_subset = {
        k: v for k, v in graph_summary_data.items() if all(v.get(key) == expected for key, expected in criteria.items())
    }
    summary_subset_list = sorted(summary_subset.keys())
    return summary_subset_list
