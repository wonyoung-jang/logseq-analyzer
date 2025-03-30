"""
Process summary data for each file based on metadata and content analysis.
"""

from typing import Any, Dict, List, Set

from .config_loader import LogseqAnalyzerConfig


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

        file_type = determine_file_type(file_path_parent_name, file_path_parts)

        is_backlinked = check_is_backlinked(name, meta_data, alphanum_dict)
        is_backlinked_by_ns_only = False
        if not is_backlinked:
            is_backlinked_by_ns_only = check_is_backlinked(name, meta_data, alphanum_dict_ns)

        node_type = "other"
        if file_type in ["journal", "page"]:
            node_type = determine_node_type(has_content, is_backlinked, is_backlinked_by_ns_only, has_backlinks)

        meta_data["file_type"] = file_type
        meta_data["node_type"] = node_type
        meta_data["has_content"] = has_content
        meta_data["has_backlinks"] = has_backlinks
        meta_data["has_external_links"] = has_external_links
        meta_data["has_embedded_links"] = has_embedded_links
        meta_data["is_backlinked"] = is_backlinked
        meta_data["is_backlinked_by_ns_only"] = is_backlinked_by_ns_only

    return graph_data


def check_is_backlinked(name: str, graph_data: Dict[str, Any], alphanum_dict: Dict[str, Set[str]]) -> bool:
    """
    Helper function to check if a file is backlinked.

    Args:
        name (str): The file name.
        graph_data (Dict[str, Any]): Graph data.
        alphanum_dict (Dict[str, Set[str]]): Dictionary for quick lookup of linked references.

    Returns:
        bool: True if the file is backlinked; otherwise, False.
    """
    id_key = graph_data["id"]
    if id_key in alphanum_dict:
        if name in alphanum_dict[id_key]:
            return True
    return False


def determine_file_type(
    file_path_parent_name: str,
    file_path_parts: List[str],
) -> str:
    """
    Helper function to determine the file type based on the directory structure.

    Args:
        file_path_parent_name (str): The parent name of the file path.
        file_path_parts (List[str]): Parts of the file path.

    Returns:
        str: The determined file type.
    """
    config = LogseqAnalyzerConfig()
    assets_dir = config.get("LOGSEQ_CONFIG", "DIR_ASSETS")
    draws_dir = config.get("LOGSEQ_CONFIG", "DIR_DRAWS")
    journals_dir = config.get("LOGSEQ_CONFIG", "DIR_JOURNALS")
    pages_dir = config.get("LOGSEQ_CONFIG", "DIR_PAGES")
    whiteboards_dir = config.get("LOGSEQ_CONFIG", "DIR_WHITEBOARDS")

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
    node_type = None

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


def extract_summary_subset_content(graph_data: Dict[str, Any], criteria) -> Dict[str, Any]:
    """
    Extract a subset of data based on a specific criteria.
    Asks: What content matches the criteria? And where is it found? How many times?

    Args:
        graph_data (Dict[str, Any]): The complete data.
        criteria (str): The criteria for extraction.

    Returns:
        Dict[str, Any]: A dictionary containing the count and locations of the extracted values.
    """
    subset_counter = {}
    for name, data in graph_data.items():
        values = data.get(criteria)
        if values:
            for value in values:
                subset_counter.setdefault(value, {})
                subset_counter[value]["count"] = subset_counter[value].get("count", 0) + 1
                subset_counter[value].setdefault("found_in", set()).add(name)
    return dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))


def extract_summary_subset_existence(graph_data: Dict[str, Any], *criteria) -> List[str]:
    """
    Extract a subset of the summary data based on whether the keys exists.
    """
    return [k for k, v in graph_data.items() if all(v.get(key) for key in criteria)]


def extract_summary_subset_key_values(graph_data: Dict[str, Any], **criteria) -> List[str]:
    """
    Extract a subset of the summary data based on multiple criteria (key-value pairs).
    """
    return [k for k, v in graph_data.items() if all(v.get(key) == expected for key, expected in criteria.items())]


def generate_summary_subsets(graph_data: dict) -> dict:
    """
    Generate summary subsets for the Logseq Analyzer.

    Args:
        graph_summary_data (dict): The graph summary data.

    Returns:
        dict: The summary data subsets.
    """
    summary_data_subsets = {}
    summary_categories = {
        # Process general categories
        "___is_backlinked": {"is_backlinked": True},
        "___is_backlinked_by_ns_only": {"is_backlinked_by_ns_only": True},
        "___has_content": {"has_content": True},
        "___has_backlinks": {"has_backlinks": True},
        "___has_external_links": {"has_external_links": True},
        "___has_embedded_links": {"has_embedded_links": True},
        # Process file types
        "___is_asset": {"file_type": "asset"},
        "___is_draw": {"file_type": "draw"},
        "___is_journal": {"file_type": "journal"},
        "___is_page": {"file_type": "page"},
        "___is_whiteboard": {"file_type": "whiteboard"},
        "___is_other": {"file_type": "other"},
        # Process nodes
        "___is_orphan_true": {"node_type": "orphan_true"},
        "___is_orphan_graph": {"node_type": "orphan_graph"},
        "___is_orphan_namespace": {"node_type": "orphan_namespace"},
        "___is_orphan_namespace_true": {"node_type": "orphan_namespace_true"},
        "___is_node_root": {"node_type": "root"},
        "___is_node_leaf": {"node_type": "leaf"},
        "___is_node_branch": {"node_type": "branch"},
        "___is_node_other": {"node_type": "other_node"},
    }

    for output_name, criteria in summary_categories.items():
        summary_data_subsets[output_name] = extract_summary_subset_key_values(graph_data, **criteria)

    # Process file extensions
    file_extensions = {}
    for meta in graph_data.values():
        ext = meta.get("file_path_suffix")
        if ext in file_extensions:
            continue
        file_extensions[ext] = True

    file_ext_dict = {}
    for ext in file_extensions:
        output_name = f"_all_{ext}s"
        criteria = {"file_path_suffix": ext}
        subset = extract_summary_subset_key_values(graph_data, **criteria)
        file_ext_dict[output_name] = subset

    summary_data_subsets["____file_extensions_dict"] = file_ext_dict

    # Process content types
    content_subset_tags_nodes = [
        "advanced_commands",
        "aliases",
        "assets",
        "block_embed",
        "block_reference",
        "blockquotes",
        "calc_block",
        "clozes",
        "draws",
        "embed",
        "embedded_links_asset",
        "embedded_links_internet",
        "embedded_links_other",
        "external_links_alias",
        "external_links_internet",
        "external_links_other",
        "file_path_parts",
        "flashcards",
        "multiline_code_block",
        "multiline_code_lang",
        "namespace_queries",
        "page_embed",
        "page_references",
        "properties_block_builtin",
        "properties_block_user",
        "properties_page_builtin",
        "properties_page_user",
        "properties_values",
        "query_functions",
        "reference",
        "simple_queries",
        "tagged_backlinks",
        "tags",
    ]

    # for criteria in ALL_DATA_POINTS:
    for criteria in content_subset_tags_nodes:
        counts_output_name = f"_content_{criteria}"
        summary_data_subsets[counts_output_name] = extract_summary_subset_content(graph_data, criteria)

    return summary_data_subsets


def generate_sorted_summary_all(graph_data: dict, reverse=True, count=-1) -> dict:
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
