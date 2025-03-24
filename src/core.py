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

    graph_dir_structure = iter_files(logseq_graph_folder, target_dirs)

    for file_path in graph_dir_structure:
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
    graph_data, alphanum_dict, alphanum_dict_ns, dangling_links, all_refs = post_processing_content(graph_data)
    graph_data = process_summary_data(graph_data, alphanum_dict, alphanum_dict_ns)

    return (
        alphanum_dict,
        alphanum_dict_ns,
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
    summary_data_subsets = {}

    # Process general categories
    summary_categories: Dict[str, Dict[str, Any]] = {
        "is_backlinked": {"is_backlinked": True},
        "is_backlinked_by_ns_only": {"is_backlinked_by_ns_only": True},
        "has_content": {"has_content": True},
        "has_backlinks": {"has_backlinks": True},
        "has_external_links": {"has_external_links": True},
        "has_embedded_links": {"has_embedded_links": True},
    }

    for output_name, criteria in summary_categories.items():
        subset = extract_summary_subset_files(graph_data, **criteria)
        summary_data_subsets[output_name] = subset

    # Process file types
    summary_categories_types: Dict[str, Dict[str, Any]] = {
        "is_asset": {"file_type": "asset"},
        "is_draw": {"file_type": "draw"},
        "is_journal": {"file_type": "journal"},
        "is_page": {"file_type": "page"},
        "is_whiteboard": {"file_type": "whiteboard"},
        "is_other": {"file_type": "other"},
    }

    for output_name, criteria in summary_categories_types.items():
        subset = extract_summary_subset_files(graph_data, **criteria)
        summary_data_subsets[output_name] = subset

    # Process nodes
    summary_categories_nodes: Dict[str, Dict[str, Any]] = {
        "is_orphan_true": {"node_type": "orphan_true"},
        "is_orphan_graph": {"node_type": "orphan_graph"},
        "is_orphan_namespace": {"node_type": "orphan_namespace"},
        "is_orphan_namespace_true": {"node_type": "orphan_namespace_true"},
        "is_node_root": {"node_type": "root"},
        "is_node_leaf": {"node_type": "leaf"},
        "is_node_branch": {"node_type": "branch"},
        "is_node_other": {"node_type": "other_node"},
    }

    for output_name, criteria in summary_categories_nodes.items():
        subset = extract_summary_subset_files(graph_data, **criteria)
        summary_data_subsets[output_name] = subset

    # Process file extensions
    file_extensions = {}
    for meta in graph_data.values():
        ext = meta.get("file_extension")
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    summary_data_subsets["file_extensions"] = file_extensions

    for ext in file_extensions:
        output_name = f"all_{ext}s"
        criteria = {"file_extension": ext}
        subset = extract_summary_subset_files(graph_data, **criteria)
        summary_data_subsets[output_name] = subset

    # TODO Testing content subset
    content_subset_tags_nodes = {
        "aliases": "aliases",
        "namespace_parts": "namespace_parts",
        "page_references": "page_references",
        "tagged_backlinks": "tagged_backlinks",
        "tags": "tags",
        "properties_values": "properties_values",
        "properties_page_builtin": "properties_page_builtin",
        "properties_page_user": "properties_page_user",
        "properties_block_builtin": "properties_block_builtin",
        "properties_block_user": "properties_block_user",
        "assets": "assets",
        "draws": "draws",
        "external_links": "external_links",
        "external_links_internet": "external_links_internet",
        "external_links_alias": "external_links_alias",
        "embedded_links": "embedded_links",
        "embedded_links_internet": "embedded_links_internet",
        "embedded_links_asset": "embedded_links_asset",
        "blockquotes": "blockquotes",
        "flashcards": "flashcards",
        "multiline_code_block": "multiline_code_block",
        "calc_block": "calc_block",
        "multiline_code_lang": "multiline_code_lang",
        "reference": "reference",
        "block_reference": "block_reference",
        "embed": "embed",
        "page_embed": "page_embed",
        "block_embed": "block_embed",
        "namespace_queries": "namespace_queries",
        "clozes": "clozes",
        "simple_queries": "simple_queries",
        "query_functions": "query_functions",
        "advanced_commands": "advanced_commands",
    }

    for output_name, criteria in content_subset_tags_nodes.items():
        subset, subset_counts = extract_summary_subset_content(graph_data, criteria)
        counts_output_name = f"{output_name}_counts"
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
