"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from pathlib import Path
from typing import Any, Dict, List, Pattern, Tuple

from .process_basic_file_data import process_single_file
from .process_content_data import post_processing_content
from .process_summary_data import extract_summary_subset_content, extract_summary_subset_files, process_summary_data


def process_graph_files(
    modded_files: Path,
    patterns: Dict[str, Pattern],
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """
    Process all files in the Logseq graph folder.

    Args:
        modded_files (Path): The modified files to process.
        patterns (dict): The compiled regex patterns.

    Returns:
        Tuple[Dict[str, Any], Dict[str, List[str]]]: A tuple containing the graph metadata and content bullets data.
    """
    graph_data = {}
    meta_content_bullets = {}

    for file_path in modded_files:
        file_data, content_bullets = process_single_file(file_path, patterns)

        name = file_data["name"]
        if name in graph_data:
            name = file_data["name_secondary"]

        graph_data[name] = file_data
        meta_content_bullets[name] = content_bullets

    return graph_data, meta_content_bullets


def core_data_analysis(
    graph_meta_data: dict,
) -> Tuple[dict, dict, dict, dict, dict]:
    """
    Process the core data analysis for the Logseq Analyzer.

    Args:
        graph_meta_data (dict): The graph data to analyze.

    Returns:
        Tuple[dict, dict, dict, dict, dict]: A tuple containing:
            - Alphanumeric dictionary.
            - Alphanumeric dictionary with namespace.
            - Dangling links.
            - Processed graph data.
            - All references.
    """
    graph_data_post, alphanum_dictionary, alphanum_dictionary_ns, dangling_links, all_refs = post_processing_content(
        graph_meta_data
    )

    graph_data = process_summary_data(graph_data_post, alphanum_dictionary, alphanum_dictionary_ns)

    return (
        alphanum_dictionary,
        alphanum_dictionary_ns,
        dangling_links,
        graph_data,
        all_refs,
    )


def generate_summary_subsets(graph_data: dict) -> dict:
    """
    Generate summary subsets for the Logseq Analyzer.

    Args:
        graph_summary_data (dict): The graph summary data.

    Returns:
        dict: The summary data subsets.
    """
    summary_categories: Dict[str, Dict[str, Any]] = {
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

    summary_data_subsets = {}
    for output_name, criteria in summary_categories.items():
        summary_data_subsets[output_name] = extract_summary_subset_files(graph_data, **criteria)

    # Process file extensions
    file_extensions = {}
    for meta in graph_data.values():
        ext = meta.get("file_extension")
        if ext in file_extensions:
            continue
        file_extensions[ext] = True

    file_ext_dict = {}
    for ext in file_extensions:
        output_name = f"_all_{ext}s"
        criteria = {"file_extension": ext}
        subset = extract_summary_subset_files(graph_data, **criteria)
        file_ext_dict[output_name] = subset
    summary_data_subsets["____file_extensions_dict"] = file_ext_dict

    # Process content types
    content_subset_tags_nodes = {
        "_all_advanced_commands": "advanced_commands",
        "_all_aliases": "aliases",
        "_all_assets": "assets",
        "_all_block_embeds": "block_embeds",
        "_all_block_references": "block_references",
        "_all_blockquotes": "blockquotes",
        "_all_calc_blocks": "calc_blocks",
        "_all_clozes": "clozes",
        "_all_draws": "draws",
        "_all_embedded_links_asset": "embedded_links_asset",
        "_all_embedded_links_internet": "embedded_links_internet",
        "_all_embedded_links_other": "embedded_links_other",
        "_all_embeds": "embeds",
        "_all_external_links_alias": "external_links_alias",
        "_all_external_links_internet": "external_links_internet",
        "_all_external_links_other": "external_links_other",
        "_all_flashcards": "flashcards",
        "_all_multiline_code_blocks": "multiline_code_blocks",
        "_all_multiline_code_langs": "multiline_code_langs",
        "_all_namespace_parts": "namespace_parts",
        "_all_namespace_queries": "namespace_queries",
        "_all_page_embeds": "page_embeds",
        "_all_page_references": "page_references",
        "_all_properties_block_builtin": "properties_block_builtin",
        "_all_properties_block_user": "properties_block_user",
        "_all_properties_page_builtin": "properties_page_builtin",
        "_all_properties_page_user": "properties_page_user",
        "_all_properties_values": "properties_values",
        "_all_query_functions": "query_functions",
        "_all_references_general": "references_general",
        "_all_simple_queries": "simple_queries",
        "_all_tagged_backlinks": "tagged_backlinks",
        "_all_tags": "tags",
    }

    for output_name, criteria in content_subset_tags_nodes.items():
        subset, subset_counts = extract_summary_subset_content(graph_data, criteria)
        counts_output_name = f"_content_{output_name}"
        summary_data_subsets[output_name] = subset
        summary_data_subsets[counts_output_name] = subset_counts

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
