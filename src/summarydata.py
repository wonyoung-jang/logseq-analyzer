import src.logseq_config as logseq_config
from typing import Any, Dict, Set, Tuple
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

    assets_dir = logseq_config.ASSETS_DIRECTORY
    draws_dir = logseq_config.DRAWS_DIRECTORY
    journals_dir = logseq_config.JOURNALS_DIRECTORY
    pages_dir = logseq_config.PAGES_DIRECTORY
    whiteboards_dir = logseq_config.WHITEBOARDS_DIRECTORY

    for name, meta_data in graph_meta_data.items():
        content_info = graph_content_data.get(name, {})
        has_content = bool(content_info)
        has_links = any(
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

        file_path_suffix = meta_data["file_path_suffix"]
        file_path_parent_name = meta_data["file_path_parent_name"]
        file_path_parts = meta_data["file_path_parts"]

        is_markdown = file_path_suffix == ".md"
        is_asset = file_path_parent_name == assets_dir or assets_dir in file_path_parts
        is_draw = file_path_parent_name == draws_dir
        is_journal = file_path_parent_name == journals_dir
        is_page = file_path_parent_name == pages_dir
        is_whiteboard = file_path_parent_name == whiteboards_dir
        is_other = not any(
            [is_markdown, is_asset, is_draw, is_journal, is_page, is_whiteboard]
        )

        is_backlinked = check_is_backlinked(name, meta_data, alphanum_dict)
        if is_markdown:
            (
                is_orphan_true,
                is_orphan_graph,
                is_node_root,
                is_node_leaf,
                is_node_branch,
            ) = determine_node_type(has_content, is_backlinked, has_links)
        else:
            is_orphan_true = is_orphan_graph = is_node_root = is_node_leaf = (
                is_node_branch
            ) = False

        graph_summary_data[name]["has_content"] = has_content
        graph_summary_data[name]["has_links"] = has_links
        graph_summary_data[name]["has_external_links"] = has_external_links
        graph_summary_data[name]["has_embedded_links"] = has_embedded_links
        graph_summary_data[name]["is_markdown"] = is_markdown
        graph_summary_data[name]["is_asset"] = is_asset
        graph_summary_data[name]["is_draw"] = is_draw
        graph_summary_data[name]["is_journal"] = is_journal
        graph_summary_data[name]["is_page"] = is_page
        graph_summary_data[name]["is_whiteboard"] = is_whiteboard
        graph_summary_data[name]["is_other"] = is_other
        graph_summary_data[name]["is_backlinked"] = is_backlinked
        graph_summary_data[name]["is_orphan_true"] = is_orphan_true
        graph_summary_data[name]["is_orphan_graph"] = is_orphan_graph
        graph_summary_data[name]["is_node_root"] = is_node_root
        graph_summary_data[name]["is_node_leaf"] = is_node_leaf
        graph_summary_data[name]["is_node_branch"] = is_node_branch

    return graph_summary_data


def check_is_backlinked(
    name: str, meta_data: Dict[str, Any], alphanum_dict: Dict[str, Set[str]]
) -> bool:
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
            if name == page_ref or str(name + "/") in page_ref:
                return True
    return False


def determine_node_type(
    has_content: bool, is_backlinked: bool, has_links: bool
) -> Tuple[bool, bool, bool, bool, bool]:
    """Helper function to determine node type based on summary data."""
    is_orphan_true = False
    is_orphan_graph = False
    is_node_root = False
    is_node_leaf = False
    is_node_branch = False

    if has_content:
        if is_backlinked:
            if has_links:
                is_node_branch = True
            else:
                is_node_leaf = True
        else:
            if has_links:
                is_node_root = True
            else:
                is_orphan_graph = True  # Orphan within the graph (has content but no backlinks or graph links)
    else:
        if not is_backlinked:
            is_orphan_true = True  # Truly orphan (no content, no backlinks)
        else:
            is_node_leaf = True  # Treat as leaf if backlinked but no content

    return is_orphan_true, is_orphan_graph, is_node_root, is_node_leaf, is_node_branch


def extract_summary_subset(
    graph_summary_data: Dict[str, Any], **criteria: Any
) -> Dict[str, Any]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).

    Args:
        graph_summary_data (Dict[str, Any]): The complete summary data.
        **criteria: Keyword arguments specifying the criteria for subset extraction.

    Returns:
        Dict[str, Any]: A subset of the summary data matching the criteria.
    """
    return {
        k: v
        for k, v in graph_summary_data.items()
        if all(v.get(key) == expected for key, expected in criteria.items())
    }
