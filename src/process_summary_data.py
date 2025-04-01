"""
Process summary data for each file based on metadata and content analysis.
"""

from typing import Any, Dict, List, Set

from ._global_objects import ANALYZER_CONFIG


def check_has_backlinks(data, has_content) -> bool:
    """
    Helper function to check if a file has backlinks.
    """
    if not has_content:
        return False

    has_backlinks = any(
        data.get(key)
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
    return has_backlinks


def check_has_external_links(data, has_content) -> bool:
    """
    Helper function to check if a file has external links.
    """
    if not has_content:
        return False

    has_external_links = any(
        data.get(key)
        for key in [
            "external_links_internet",
            "external_links_alias",
            "external_links_other",
        ]
    )
    return has_external_links


def check_has_embedded_links(data, has_content) -> bool:
    """
    Helper function to check if a file has embedded links.
    """
    if not has_content:
        return False

    has_embedded_links = any(
        data.get(key)
        for key in [
            "embedded_links_internet",
            "embedded_links_asset",
            "embedded_links_other",
        ]
    )
    return has_embedded_links


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
                subset_counter[value].setdefault("found_in", []).append(name)
    return dict(sorted(subset_counter.items(), key=lambda item: item[1]["count"], reverse=True))


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


def generate_summary_subsets(graph_data: Dict[str, Any]) -> Dict[str, Any]:
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
        "___is_filetype_asset": {"file_type": "asset"},
        "___is_filetype_draw": {"file_type": "draw"},
        "___is_filetype_journal": {"file_type": "journal"},
        "___is_filetype_page": {"file_type": "page"},
        "___is_filetype_whiteboard": {"file_type": "whiteboard"},
        "___is_filetype_other": {"file_type": "other"},
        # Process nodes
        "___is_node_orphan_true": {"node_type": "orphan_true"},
        "___is_node_orphan_graph": {"node_type": "orphan_graph"},
        "___is_node_orphan_namespace": {"node_type": "orphan_namespace"},
        "___is_node_orphan_namespace_true": {"node_type": "orphan_namespace_true"},
        "___is_node_root": {"node_type": "root"},
        "___is_node_leaf": {"node_type": "leaf"},
        "___is_node_branch": {"node_type": "branch"},
        "___is_node_other": {"node_type": "other_node"},
    }

    for output_name, criteria in summary_categories.items():
        summary_data_subsets[output_name] = list_files_with_keys_and_values(graph_data, **criteria)

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
        subset = list_files_with_keys_and_values(graph_data, **criteria)
        file_ext_dict[output_name] = subset

    summary_data_subsets["____file_extensions_dict"] = file_ext_dict

    # Process content types
    content_subset_tags_nodes = [
        "advanced_commands",
        "advanced_commands_export",
        "advanced_commands_export_ascii",
        "advanced_commands_export_latex",
        "advanced_commands_caution",
        "advanced_commands_center",
        "advanced_commands_comment",
        "advanced_commands_important",
        "advanced_commands_note",
        "advanced_commands_pinned",
        "advanced_commands_query",
        "advanced_commands_quote",
        "advanced_commands_tip",
        "advanced_commands_verse",
        "advanced_commands_warning",
        "aliases",
        "assets",
        "block_embeds",
        "block_references",
        "blockquotes",
        "calc_blocks",
        "clozes",
        "draws",
        "embeds",
        "embedded_links_asset",
        "embedded_links_internet",
        "embedded_links_other",
        "external_links_alias",
        "external_links_internet",
        "external_links_other",
        "file_path_parts",
        "flashcards",
        "multiline_code_blocks",
        "multiline_code_langs",
        "namespace_queries",
        "page_embeds",
        "page_references",
        "properties_block_builtin",
        "properties_block_user",
        "properties_page_builtin",
        "properties_page_user",
        "properties_values",
        "query_functions",
        "references_general",
        "simple_queries",
        "tagged_backlinks",
        "tags",
        "inline_code_blocks",
        "dynamic_variables",
        "macros",
        "embed_video_urls",
        "cards",
        "embed_twitter_tweets",
        "embed_youtube_timestamps",
        "renderers",
    ]

    # for criteria in ALL_DATA_POINTS:
    for criteria in content_subset_tags_nodes:
        counts_output_name = f"_content_{criteria}"
        summary_data_subsets[counts_output_name] = extract_summary_subset_content(graph_data, criteria)

    return summary_data_subsets


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
