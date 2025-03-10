import argparse
import logging
from pathlib import Path
from typing import Tuple, Dict, List, Pattern, Any
from src.helpers import iter_files, move_unlinked_assets, move_all_folder_content
from src.reporting import write_output
from src.filedata import process_single_file
from src.contentdata import process_content_data
from src.summarydata import process_summary_data, extract_summary_subset
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
    graph_meta_data = {}
    meta_graph_content = {}
    meta_primary_bullet = {}
    meta_content_bullets = {}

    graph_dir_structure = iter_files(logseq_graph_folder, target_dirs)

    for file_path in graph_dir_structure:
        meta_data, graph_content, primary_bullet, content_bullets = process_single_file(file_path, patterns)

        name = meta_data["name"]
        if name in graph_meta_data:
            name = meta_data["name_secondary"]

        graph_meta_data[name] = meta_data
        meta_graph_content[name] = graph_content
        meta_primary_bullet[name] = primary_bullet
        meta_content_bullets[name] = content_bullets

    return graph_meta_data, meta_graph_content, meta_primary_bullet, meta_content_bullets


def core_data_analysis(
    patterns: Dict[str, Pattern], graph_meta_data: dict, meta_graph_content: dict
) -> Tuple[Dict[str, set], List[str], dict, dict]:
    """
    Process the core data analysis for the Logseq Analyzer.

    Args:
        patterns (dict): The compiled regex patterns.
        graph_meta_data (dict): The graph metadata.
        meta_graph_content (dict): The graph content data.

    Returns:
        Tuple[dict, dict, dict, dict]: The core data analysis results.
    """
    built_in_properties = config.BUILT_IN_PROPERTIES
    graph_content_data, meta_alphanum_dictionary, meta_dangling_links = process_content_data(
        meta_graph_content, patterns, built_in_properties
    )
    graph_summary_data = process_summary_data(graph_meta_data, graph_content_data, meta_alphanum_dictionary)

    return (
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_content_data,
        graph_summary_data,
    )


def write_initial_outputs(
    args,
    output_dir,
    meta_alphanum_dictionary,
    meta_dangling_links,
    meta_graph_content,
    graph_meta_data,
    graph_content_data,
    graph_summary_data,
    target_dirs,
    meta_primary_bullet,
    meta_content_bullets,
) -> None:
    """Write initial outputs for graph analysis to specified directories.

    Args:
        args: Arguments containing write_graph flag
        output_dir (str): Base directory for output files
        meta_alphanum_dictionary (dict): Dictionary of alphanumeric metadata
        meta_dangling_links (list): List of dangling links in the graph
        meta_graph_content (dict): Content of the graph metadata
        graph_meta_data (dict): Metadata about the graph structure
        graph_content_data (dict): Content data for graph nodes
        graph_summary_data (dict): Summary statistics of the graph
        meta_primary_bullet (dict): Primary bullet data for graph nodes
        meta_content_bullets (dict): Content bullet data for graph nodes
    """
    if args.write_graph:
        write_output(output_dir, "graph_content", meta_graph_content, config.OUTPUT_DIR_META)

    write_output(output_dir, "alphanum_dictionary", meta_alphanum_dictionary, config.OUTPUT_DIR_META)
    write_output(output_dir, "dangling_links", meta_dangling_links, config.OUTPUT_DIR_META)
    write_output(output_dir, "target_dirs", target_dirs, config.OUTPUT_DIR_META)
    write_output(output_dir, "meta_primary_bullet", meta_primary_bullet, config.OUTPUT_DIR_META)
    write_output(output_dir, "meta_content_bullets", meta_content_bullets, config.OUTPUT_DIR_META)

    write_output(output_dir, "01_meta_data", graph_meta_data, config.OUTPUT_DIR_GRAPH)
    write_output(output_dir, "02_content_data", graph_content_data, config.OUTPUT_DIR_GRAPH)
    write_output(output_dir, "03_summary_data", graph_summary_data, config.OUTPUT_DIR_GRAPH)


def generate_summary_subsets(output_dir: Path, graph_summary_data: dict) -> dict:
    """
    Generate summary subsets for the Logseq Analyzer.

    Args:
        output_dir (Path): The output directory.
        graph_summary_data (dict): The graph summary data.

    Returns:
        dict: The summary data subsets.
    """
    summary_data_subsets = {}

    # Process general categories
    summary_categories: Dict[str, Dict[str, Any]] = {
        "is_backlinked": {"is_backlinked": True},
        "has_content": {"has_content": True},
        "has_backlinks": {"has_backlinks": True},
        "has_external_links": {"has_external_links": True},
        "has_embedded_links": {"has_embedded_links": True},
    }

    for output_name, criteria in summary_categories.items():
        subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = subset
        write_output(output_dir, output_name, subset, config.OUTPUT_DIR_SUMMARY)

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
        subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = subset
        write_output(output_dir, output_name, subset, config.OUTPUT_DIR_TYPES)

    # Process nodes
    summary_categories_nodes: Dict[str, Dict[str, Any]] = {
        "is_orphan_true": {"node_type": "orphan_true"},
        "is_orphan_graph": {"node_type": "orphan_graph"},
        "is_node_root": {"node_type": "root"},
        "is_node_leaf": {"node_type": "leaf"},
        "is_node_branch": {"node_type": "branch"},
        "is_node_other": {"node_type": "other-node"},
    }

    for output_name, criteria in summary_categories_nodes.items():
        subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = subset
        write_output(output_dir, output_name, subset, config.OUTPUT_DIR_NODES)

    # Process file extensions
    file_extensions = {}
    for meta in graph_summary_data.values():
        ext = meta.get("file_extension")
        file_extensions[ext] = file_extensions.get(ext, 0) + 1
    summary_data_subsets["file_extensions"] = file_extensions
    write_output(output_dir, "_file_extensions_oveview", file_extensions, config.OUTPUT_DIR_EXTENSIONS)

    for ext in file_extensions:
        output_name = f"all_{ext}s"
        criteria = {"file_extension": ext}
        subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = subset
        write_output(output_dir, output_name, subset, config.OUTPUT_DIR_EXTENSIONS)

    return summary_data_subsets


def generate_global_summary(output_dir: Path, summary_data_subsets: dict) -> None:
    """
    Generate a global summary for the Logseq Analyzer.

    Args:
        output_dir (Path): The output directory.
        summary_data_subsets (dict): The summary data subsets.
    """
    global_summary: Dict[str, Dict[str, int]] = {}
    for subset_name, subset in summary_data_subsets.items():
        global_summary[subset_name] = {}
        global_summary[subset_name]["results"] = len(subset)

    write_output(output_dir, "global_summary", global_summary, config.OUTPUT_DIR_SUMMARY)


def handle_assets(
    args: argparse.Namespace,
    output_dir: Path,
    graph_meta_data: dict,
    graph_content_data: dict,
    graph_summary_data: dict,
    summary_data_subsets: dict,
    to_delete_dir: Path,
) -> None:
    """
    Handle assets for the Logseq Analyzer.

    Args:
        args (argparse.Namespace): The command line arguments.
        output_dir (Path): The output directory.
        graph_meta_data (dict): The graph metadata.
        graph_content_data (dict): The graph content data.
        graph_summary_data (dict): The graph summary data.
        summary_data_subsets (dict): The summary data subsets.
        to_delete_dir (Path): The directory for deleted files.
    """
    summary_is_asset = summary_data_subsets["is_asset"]
    not_referenced_assets_keys = list(summary_is_asset.keys())
    for content_data in graph_content_data.values():
        if not content_data["assets"]:
            continue
        for non_asset in not_referenced_assets_keys:
            non_asset_secondary = graph_meta_data[non_asset]["name"]
            for asset_mention in content_data["assets"]:
                if graph_summary_data[non_asset]["is_backlinked"]:
                    continue

                if non_asset in asset_mention or non_asset_secondary in asset_mention:
                    graph_summary_data[non_asset]["is_backlinked"] = True
                    break

    summary_is_asset_backlinked = extract_summary_subset(graph_summary_data, file_type="asset", is_backlinked=True)
    summary_is_asset_not_backlinked = extract_summary_subset(graph_summary_data, file_type="asset", is_backlinked=False)

    write_output(
        output_dir,
        "is_asset_backlinked",
        summary_is_asset_backlinked,
        config.OUTPUT_DIR_ASSETS,
    )
    write_output(
        output_dir,
        "is_asset_not_backlinked",
        summary_is_asset_not_backlinked,
        config.OUTPUT_DIR_ASSETS,
    )

    # Optional move unlinked assets
    if args.move_unlinked_assets:
        move_unlinked_assets(summary_is_asset_not_backlinked, graph_meta_data, to_delete_dir)


def handle_bak_recycle(args: argparse.Namespace, bak: Path, recycle: Path, to_delete_dir: Path) -> None:
    """
    Handle bak and recycle files for the Logseq Analyzer.

    Args:
        args (argparse.Namespace): The command line arguments.
        bak (Path): The bak directory.
        recycle (Path): The recycle directory.
        to_delete_dir (Path): The directory for deleted files.
    """
    if args.move_bak:
        move_all_folder_content(bak, to_delete_dir, Path(config.DEFAULT_BAK_DIR))

    if args.move_recycle:
        move_all_folder_content(recycle, to_delete_dir, Path(config.DEFAULT_RECYCLE_DIR))


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
