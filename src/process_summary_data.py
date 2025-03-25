"""
Process summary data for each file based on metadata and content analysis.
"""

from typing import Any, Dict, List, Set, Tuple

from .config_loader import get_config

CONFIG = get_config()


def process_summary_data(
    graph_data: Dict[str, Any],
    alphanum_dict: Dict[str, Set[str]],
    alphanum_dict_ns: Dict[str, Set[str]],
) -> Dict[str, Any]:
    """
    Process summary data for each file based on metadata and content analysis.

    Categorizes files and determines node types (root, leaf, branch, orphan).

    Args:
        graph_data (Dict[str, Any]): Metadata for each file.
        alphanum_dict (Dict[str, Set[str]]): Dictionary for quick lookup of linked references.
        alphanum_dict_ns (Dict[str, Set[str]]): Dictionary for quick lookup of linked references in namespaces.

    Returns:
        Dict[str, Any]: Summary data for each file.
    """
    assets_dir = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_ASSETS")
    draws_dir = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_DRAWS")
    journals_dir = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_JOURNALS")
    pages_dir = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_PAGES")
    whiteboards_dir = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_WHITEBOARDS")
    file_type_journal = CONFIG.get("FILE_TYPES", "JOURNAL")
    file_type_page = CONFIG.get("FILE_TYPES", "PAGE")

    for name, meta_data in graph_data.items():
        has_content = bool(meta_data["size"] > 0)
        has_backlinks = False
        has_external_links = False
        has_embedded_links = False
        if has_content:
            has_backlinks = any(
                meta_data.get(key)
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
                meta_data.get(key)
                for key in [
                    "external_links",
                    "external_links_internet",
                    "external_links_alias",
                ]
            )
            has_embedded_links = any(
                meta_data.get(key)
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
        is_backlinked_by_ns_only = False
        if not is_backlinked:
            is_backlinked_by_ns_only = check_is_backlinked(name, meta_data, alphanum_dict_ns)

        node_type = CONFIG.get("NODE_TYPES", "OTHER")
        if file_type in [file_type_journal, file_type_page]:
            node_type = determine_node_type(has_content, is_backlinked, is_backlinked_by_ns_only, has_backlinks)

        meta_data["file_type"] = file_type
        meta_data["file_extension"] = meta_data["file_path_suffix"]
        meta_data["node_type"] = node_type
        meta_data["has_content"] = has_content
        meta_data["has_backlinks"] = has_backlinks
        meta_data["has_external_links"] = has_external_links
        meta_data["has_embedded_links"] = has_embedded_links
        meta_data["is_backlinked"] = is_backlinked
        meta_data["is_backlinked_by_ns_only"] = is_backlinked_by_ns_only

    return graph_data


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
            if name == page_ref:
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
        file_type = CONFIG.get("FILE_TYPES", "ASSET")
    elif file_path_parent_name == draws_dir:
        file_type = CONFIG.get("FILE_TYPES", "DRAW")
    elif file_path_parent_name == journals_dir:
        file_type = CONFIG.get("FILE_TYPES", "JOURNAL")
    elif file_path_parent_name == pages_dir:
        file_type = CONFIG.get("FILE_TYPES", "PAGE")
    elif file_path_parent_name == whiteboards_dir:
        file_type = CONFIG.get("FILE_TYPES", "WHITEBOARD")
    else:
        file_type = CONFIG.get("FILE_TYPES", "OTHER")
    return file_type


def determine_node_type(has_content: bool, is_backlinked: bool, is_backlinked_ns: bool, has_backlinks: bool) -> str:
    """Helper function to determine node type based on summary data."""
    if has_content:
        if is_backlinked:
            if has_backlinks:
                return CONFIG.get("NODE_TYPES", "BRANCH")
            return CONFIG.get("NODE_TYPES", "LEAF")
        if has_backlinks:
            return CONFIG.get("NODE_TYPES", "ROOT")
        if is_backlinked_ns:
            return CONFIG.get("NODE_TYPES", "ORPHAN_NS")
        return CONFIG.get("NODE_TYPES", "ORPHAN_GRAPH")

    if not is_backlinked:
        if is_backlinked_ns:
            return CONFIG.get("NODE_TYPES", "ORPHAN_NS_TRUE")
        return CONFIG.get("NODE_TYPES", "ORPHAN_TRUE")
    return CONFIG.get("NODE_TYPES", "LEAF")


def extract_summary_subset_content(graph_data: Dict[str, Any], criteria) -> Tuple[List[str], Dict[str, Dict]]:
    """
    Extract a subset of data based on a specific criteria.
    Asks: What content matches the criteria? And where is it found? How many times?

    Args:
        graph_data (Dict[str, Any]): The complete data.
        criteria (str): The criteria for extraction.

    Returns:
        Tuple[List[str], Dict[str, Dict]]: A tuple containing a sorted list of
        unique values and a dictionary with counts and locations.
    """
    subset = set()
    subset_counter = {}
    for k, v in graph_data.items():
        values = v.get(criteria)
        if values:
            subset.update(values)
            for value in values:
                subset_counter[value] = subset_counter.get(value, {})
                subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                subset_counter[value]["found_in"] = subset_counter[value].get("found_in", set())
                subset_counter[value]["found_in"].add(k)

    sorted_subset = sorted(subset)
    sorted_subset_counter = dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))

    return sorted_subset, sorted_subset_counter


def extract_summary_subset_files(graph_data: Dict[str, Any], **criteria) -> List[str]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).
    Asks: What files match the criteria?

    Args:
        graph_data (Dict[str, Any]): The complete summary data.
        **criteria: Keyword arguments specifying the criteria for subset extraction.

    Returns:
        List[str]: A list of keys from the summary data that match the criteria.
    """
    subset = {k: v for k, v in graph_data.items() if all(v.get(key) == expected for key, expected in criteria.items())}
    sorted_subset = sorted(subset.keys())

    return sorted_subset
