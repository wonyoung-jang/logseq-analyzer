"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from pathlib import Path
from typing import Any, Dict, List, Pattern, Tuple

from .helpers import iter_files
from .process_basic_file_data import process_single_file
from .process_content_data import post_processing_content
from .process_summary_data import extract_summary_subset_content, extract_summary_subset_files, process_summary_data


def process_graph_files(
    logseq_graph_folder: Path, patterns: Dict[str, Pattern], target_dirs: List[str]
) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    """
    Process all files in the Logseq graph folder.

    Args:
        logseq_graph_folder (Path): The path to the Logseq graph folder.
        patterns (dict): The compiled regex patterns.
        target_dirs (List[str]): The target directories to process.

    Returns:
        Tuple[Dict[str, Any], Dict[str, List[str]]]: A tuple containing the graph metadata and content bullets data.
    """
    graph_data = {}
    meta_content_bullets = {}

    for file_path in iter_files(logseq_graph_folder, target_dirs):
        file_data, content_bullets = process_single_file(file_path, patterns)

        name = file_data["name"]
        if name in graph_data:
            name = file_data["name_secondary"]

        graph_data[name] = file_data
        meta_content_bullets[name] = content_bullets

    return graph_data, meta_content_bullets


def core_data_analysis(
    graph_data: dict,
) -> Tuple[dict, dict, dict, dict, dict]:
    """
    Process the core data analysis for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data to analyze.

    Returns:
        Tuple[dict, dict, dict, dict, dict]: A tuple containing:
            - Alphanumeric dictionary.
            - Alphanumeric dictionary with namespace.
            - Dangling links.
            - Processed graph data.
            - All references.
    """
    graph_data, alphanum_dictionary, alphanum_dictionary_ns, dangling_links, all_refs = post_processing_content(
        graph_data
    )
    graph_data = process_summary_data(graph_data, alphanum_dictionary, alphanum_dictionary_ns)

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
        "_is_backlinked": {"is_backlinked": True},
        "_is_backlinked_by_ns_only": {"is_backlinked_by_ns_only": True},
        "_has_content": {"has_content": True},
        "_has_backlinks": {"has_backlinks": True},
        "_has_external_links": {"has_external_links": True},
        "_has_embedded_links": {"has_embedded_links": True},
        # Process file types
        "_is_asset": {"file_type": "asset"},
        "_is_draw": {"file_type": "draw"},
        "_is_journal": {"file_type": "journal"},
        "_is_page": {"file_type": "page"},
        "_is_whiteboard": {"file_type": "whiteboard"},
        "_is_other": {"file_type": "other"},
        # Process nodes
        "_is_orphan_true": {"node_type": "orphan_true"},
        "_is_orphan_graph": {"node_type": "orphan_graph"},
        "_is_orphan_namespace": {"node_type": "orphan_namespace"},
        "_is_orphan_namespace_true": {"node_type": "orphan_namespace_true"},
        "_is_node_root": {"node_type": "root"},
        "_is_node_leaf": {"node_type": "leaf"},
        "_is_node_branch": {"node_type": "branch"},
        "_is_node_other": {"node_type": "other_node"},
    }

    summary_data_subsets = {}
    for output_name, criteria in summary_categories.items():
        summary_data_subsets[output_name] = extract_summary_subset_files(graph_data, **criteria)

    # Process file extensions
    file_extensions = {}
    for meta in graph_data.values():
        ext = meta.get("file_extension")
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    summary_data_subsets["_file_extensions"] = file_extensions

    for ext in file_extensions:
        output_name = f"_all_{ext}s"
        criteria = {"file_extension": ext}
        subset = extract_summary_subset_files(graph_data, **criteria)
        summary_data_subsets[output_name] = subset

    # Process content types
    content_subset_tags_nodes = {
        "advanced_commands": "advanced_commands",
        "aliases": "aliases",
        "assets": "assets",
        "block_embeds": "block_embeds",
        "block_references": "block_references",
        "blockquotes": "blockquotes",
        "calc_blocks": "calc_blocks",
        "clozes": "clozes",
        "draws": "draws",
        "embedded_links_asset": "embedded_links_asset",
        "embedded_links_internet": "embedded_links_internet",
        "embedded_links_other": "embedded_links_other",
        "embeds": "embeds",
        "external_links_alias": "external_links_alias",
        "external_links_internet": "external_links_internet",
        "external_links_other": "external_links_other",
        "flashcards": "flashcards",
        "multiline_code_blocks": "multiline_code_blocks",
        "multiline_code_langs": "multiline_code_langs",
        "namespace_parts": "namespace_parts",
        "namespace_queries": "namespace_queries",
        "page_embeds": "page_embeds",
        "page_references": "page_references",
        "properties_block_builtin": "properties_block_builtin",
        "properties_block_user": "properties_block_user",
        "properties_page_builtin": "properties_page_builtin",
        "properties_page_user": "properties_page_user",
        "properties_values": "properties_values",
        "query_functions": "query_functions",
        "references_general": "references_general",
        "simple_queries": "simple_queries",
        "tagged_backlinks": "tagged_backlinks",
        "tags": "tags",
    }

    for output_name, criteria in content_subset_tags_nodes.items():
        subset, subset_counts = extract_summary_subset_content(graph_data, criteria)
        counts_output_name = f"counts_{output_name}"
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


def generate_global_summary(summary_data_subsets: dict) -> dict:
    """
    Generate a global summary for the Logseq Analyzer.

    Args:
        summary_data_subsets (dict): The summary data subsets.
    """
    global_summary = {}
    for subset_name, subset in summary_data_subsets.items():
        global_summary[subset_name] = {}
        global_summary[subset_name]["results"] = len(subset)
    return global_summary
