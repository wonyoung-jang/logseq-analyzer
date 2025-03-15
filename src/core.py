import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Pattern

from src.helpers import iter_files, move_unlinked_assets, move_all_folder_content
from src.reporting import write_output
from src.process_basic_file_data import process_single_file
from src.process_content_data import post_processing_content
from src.process_summary_data import extract_summary_subset_content, process_summary_data, extract_summary_subset_files
import src.config as config


def process_graph_files(
    logseq_graph_folder: Path, patterns: Dict[str, Pattern], target_dirs: List[str]
) -> Tuple[dict, dict, dict, dict]:
    """
    Process all files in the Logseq graph folder.

    Args:
        logseq_graph_folder (Path): The path to the Logseq graph folder.
        patterns (dict): The compiled regex patterns.
        target_dirs (List[str]): The target directories to process.

    Returns:
        Tuple[dict, dict, dict, dict]: A tuple containing the graph metadata, content data, primary bullet data, and content bullets data.
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
) -> Tuple[Dict[str, set], List[str], dict, dict]:
    """
    Process the core data analysis for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data to analyze.

    Returns:
        Tuple[dict, dict, dict, dict]: The core data analysis results.
    """
    graph_data, alphanum_dict, alphanum_dict_ns, dangling_links = post_processing_content(graph_data)
    graph_data = process_summary_data(graph_data, alphanum_dict, alphanum_dict_ns)

    return (
        alphanum_dict,
        alphanum_dict_ns,
        dangling_links,
        graph_data,
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
        write_output(config.DEFAULT_OUTPUT_DIR, output_name, subset, config.OUTPUT_DIR_SUMMARY)

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
        write_output(config.DEFAULT_OUTPUT_DIR, output_name, subset, config.OUTPUT_DIR_TYPES)

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
        write_output(config.DEFAULT_OUTPUT_DIR, output_name, subset, config.OUTPUT_DIR_NODES)

    # Process file extensions
    file_extensions = {}
    for meta in graph_data.values():
        ext = meta.get("file_extension")
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    summary_data_subsets["file_extensions"] = file_extensions
    write_output(config.DEFAULT_OUTPUT_DIR, "_file_extensions_oveview", file_extensions, config.OUTPUT_DIR_EXTENSIONS)

    for ext in file_extensions:
        output_name = f"all_{ext}s"
        criteria = {"file_extension": ext}
        subset = extract_summary_subset_files(graph_data, **criteria)
        summary_data_subsets[output_name] = subset
        write_output(config.DEFAULT_OUTPUT_DIR, output_name, subset, config.OUTPUT_DIR_EXTENSIONS)

    # TODO Testing content subset
    content_subset_tags_nodes = {
        "aliases": "aliases",
        # "namespace_root": "namespace_root",
        # "namespace_parent": "namespace_parent",
        "namespace_parts": "namespace_parts",
        # "namespace_level": "namespace_level",
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
        write_output(config.DEFAULT_OUTPUT_DIR, output_name, subset, config.OUTPUT_DIR_CONTENTS)
        write_output(config.DEFAULT_OUTPUT_DIR, counts_output_name, subset_counts, config.OUTPUT_DIR_CONTENTS_COUNTS)

    return summary_data_subsets


def generate_sorted_summary(graph_data: dict, target, attribute, reverse=True, count=-1) -> None:
    """
    Generate a sorted summary for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data to analyze.
        target (str): The target directory for the output files.
        attribute (str): The attribute to sort by.
    """
    sorted_data = {}
    for name, data in graph_data.items():
        if attribute in data:
            if isinstance(data[attribute], (list, dict, set)):
                sorted_data[name] = len(data[attribute])
            elif isinstance(data[attribute], str):
                sorted_data[name] = 1
            else:
                sorted_data[name] = data[attribute]

    sorted_data = dict(sorted(sorted_data.items(), key=lambda item: item[1], reverse=reverse))
    if count > 0:
        sub_sorted_data = dict(sorted(sorted_data.items(), key=lambda item: item[1], reverse=reverse)[:count])
        write_output(config.DEFAULT_OUTPUT_DIR, f"sorted_{attribute}", sub_sorted_data, target)
    else:
        write_output(config.DEFAULT_OUTPUT_DIR, f"sorted_{attribute}", sorted_data, target)

    return sorted_data


def generate_sorted_summary_statistics(sorted_data: dict, target, attribute) -> None:
    """
    Generate a sorted summary statistics for the Logseq Analyzer.

    Args:
        sorted_data (dict): The sorted data to analyze.
        target (str): The target directory for the output files.
        attribute (str): The attribute to sort by.
    """
    sorted_values = list(sorted_data.values())
    minimum = min(sorted_values)
    maximum = max(sorted_values)
    mean = sum(sorted_values) / len(sorted_values)
    median = sorted_values[len(sorted_values) // 2]
    variance = sum((x - mean) ** 2 for x in sorted_values) / len(sorted_values)
    stddev = variance**0.5

    stats = {
        "min": minimum,
        "mean": round(mean, 2),
        "median": round(median, 2),
        "max": maximum,
        "stddev": round(stddev, 2),
    }

    write_output(config.DEFAULT_OUTPUT_DIR, f"{attribute}_statistics", stats, target)


def generate_global_summary(summary_data_subsets: dict, target=config.OUTPUT_DIR_SUMMARY) -> None:
    """
    Generate a global summary for the Logseq Analyzer.

    Args:
        summary_data_subsets (dict): The summary data subsets.
        target (str): The target directory for the output files.
    """
    global_summary: Dict[str, Dict[str, int]] = {}
    for subset_name, subset in summary_data_subsets.items():
        global_summary[subset_name] = {}
        global_summary[subset_name]["results"] = len(subset)

    write_output(config.DEFAULT_OUTPUT_DIR, "global_summary", global_summary, target)


def handle_assets(
    graph_data: dict,
    summary_data_subsets: dict,
    to_delete_dir: Path,
) -> None:
    """
    Handle assets for the Logseq Analyzer.

    Args:
        graph_data (dict): The graph data.
        summary_data_subsets (dict): The summary data subsets.
        to_delete_dir (Path): The directory for deleted files.
    """
    if not to_delete_dir:
        return

    summary_is_asset = summary_data_subsets["is_asset"]
    for content_data in graph_data.values():
        if not content_data["assets"]:
            continue

        for non_asset in summary_is_asset:
            non_asset_secondary = graph_data[non_asset]["name"]

            for asset_mention in content_data["assets"]:
                if graph_data[non_asset]["is_backlinked"]:
                    continue

                if non_asset in asset_mention or non_asset_secondary in asset_mention:
                    graph_data[non_asset]["is_backlinked"] = True
                    break

    asset_backlinked_kwargs = {
        "is_backlinked": True,
        "file_type": "asset",
    }
    asset_not_backlinked_kwargs = {
        "is_backlinked": False,
        "file_type": "asset",
    }
    summary_is_asset_backlinked = extract_summary_subset_files(graph_data, **asset_backlinked_kwargs)
    summary_is_asset_not_backlinked = extract_summary_subset_files(graph_data, **asset_not_backlinked_kwargs)

    write_output(
        config.DEFAULT_OUTPUT_DIR,
        "is_asset_backlinked",
        summary_is_asset_backlinked,
        config.OUTPUT_DIR_ASSETS,
    )
    write_output(
        config.DEFAULT_OUTPUT_DIR,
        "is_asset_not_backlinked",
        summary_is_asset_not_backlinked,
        config.OUTPUT_DIR_ASSETS,
    )

    return summary_is_asset_not_backlinked


def handle_move_files(
    args: argparse.Namespace, graph_meta_data: dict, assets: dict, bak: Path, recycle: Path, to_delete_dir: Path
) -> None:
    """
    Handle the moving of unlinked assets, bak, and recycle files to a specified directory.

    Args:
        args (argparse.Namespace): The command line arguments.
        graph_meta_data (dict): The graph metadata.
        assets (dict): The assets data.
        bak (Path): The path to the bak directory.
        recycle (Path): The path to the recycle directory.
        to_delete_dir (Path): The directory for deleted files.
    """
    if not to_delete_dir:
        return

    moved_files = {}
    if args.move_unlinked_assets:
        moved_assets = move_unlinked_assets(assets, graph_meta_data, to_delete_dir)
        if moved_assets:
            moved_files["moved_assets"] = moved_assets

    if args.move_bak:
        moved_bak = move_all_folder_content(bak, to_delete_dir, Path(config.DEFAULT_BAK_DIR))
        if moved_bak:
            moved_files["moved_bak"] = moved_bak

    if args.move_recycle:
        moved_recycle = move_all_folder_content(recycle, to_delete_dir, Path(config.DEFAULT_RECYCLE_DIR))
        if moved_recycle:
            moved_files["moved_recycle"] = moved_recycle

    write_output(
        config.DEFAULT_OUTPUT_DIR,
        "moved_files",
        moved_files,
        config.OUTPUT_DIR_META,
    )


def create_delete_directory() -> Path:
    """
    Create a directory for deleted files.

    Returns:
        Path: The path to the delete directory.
    """
    delete_dir = Path(config.DEFAULT_TO_DELETE_DIR)
    if not delete_dir.exists():
        logging.info(f"Creating directory: {delete_dir}")
        delete_dir.mkdir(parents=True, exist_ok=True)
    return delete_dir
