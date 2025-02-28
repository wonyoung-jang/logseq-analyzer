import argparse
import logging
from pathlib import Path
from typing import Tuple, Dict, List, Pattern
from src.helpers import iter_files, extract_logseq_config_edn, move_unlinked_assets, extract_logseq_bak_recycle, move_all_folder_content
from src.compile_regex import compile_regex_patterns
from src.setup import setup_logging, setup_output_directory
from src.reporting import write_output
from src.filedata import process_single_file
from src.contentdata import process_content_data
from src.summarydata import process_summary_data, extract_summary_subset
import src.config as config


def run_app():
    """
    Main function to run the Logseq analyzer.
    """
    args = setup_logseq_analyzer_args()

    logseq_graph_folder, output_dir = setup_logging_and_output(args)

    target_dirs = extract_logseq_config_edn(logseq_graph_folder)

    recycle, bak = extract_logseq_bak_recycle(logseq_graph_folder)

    patterns = compile_regex_patterns()

    graph_meta_data, meta_graph_content = process_graph_files(logseq_graph_folder, patterns, target_dirs)

    (
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_content_data,
        graph_summary_data,
    ) = core_data_analysis(patterns, graph_meta_data, meta_graph_content)

    write_initial_outputs(
        args,
        output_dir,
        meta_alphanum_dictionary,
        meta_dangling_links,
        meta_graph_content,
        graph_meta_data,
        graph_content_data,
        graph_summary_data,
    )

    summary_data_subsets = generate_summary_subsets(output_dir, graph_summary_data)

    handle_assets(args, output_dir, graph_meta_data, graph_content_data, graph_summary_data, summary_data_subsets)

    handle_bak_recycle(args, bak, recycle)

    logging.info("Logseq Analyzer completed.")


def handle_bak_recycle(args: argparse.Namespace, bak: Path, recycle: Path) -> None:
    """
    Handle bak and recycle files for the Logseq Analyzer.

    Args:
        args (argparse.Namespace): The command line arguments.
        bak (Path): The bak directory.
        recycle (Path): The recycle directory.
    """
    to_delete_dir = Path(config.DEFAULT_TO_DELETE_DIR)
    if not to_delete_dir.exists():
        to_delete_dir.mkdir()
        logging.info(f"Created directory: {to_delete_dir}")

    if args.move_bak:
        move_all_folder_content(bak, to_delete_dir)

    if args.move_recycle:
        move_all_folder_content(recycle, to_delete_dir)


def handle_assets(
    args: argparse.Namespace,
    output_dir: Path,
    graph_meta_data: dict,
    graph_content_data: dict,
    graph_summary_data: dict,
    summary_data_subsets: dict,
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
    """
    summary_is_asset = summary_data_subsets["is_asset"]
    not_referenced_assets_keys = list(summary_is_asset.keys())
    for name, content_data in graph_content_data.items():
        if not content_data["assets"]:
            continue
        for non_asset in not_referenced_assets_keys:
            non_asset_secondary = graph_meta_data[non_asset]["name"]
            for asset_mention in content_data["assets"]:
                if non_asset in asset_mention or non_asset_secondary in asset_mention:
                    graph_summary_data[non_asset]["is_backlinked"] = True
                    break

    summary_is_asset_backlinked = extract_summary_subset(graph_summary_data, file_type="asset", is_backlinked=True)
    summary_is_asset_not_backlinked = extract_summary_subset(graph_summary_data, file_type="asset", is_backlinked=False)
    write_output(
        output_dir,
        "is_asset_backlinked",
        summary_is_asset_backlinked,
        config.OUTPUT_DIR_SUMMARY,
    )
    write_output(
        output_dir,
        "is_asset_not_backlinked",
        summary_is_asset_not_backlinked,
        config.OUTPUT_DIR_SUMMARY,
    )

    # Optional move unlinked assets
    if args.move_unlinked_assets:
        move_unlinked_assets(summary_is_asset_not_backlinked, graph_meta_data)


def generate_summary_subsets(output_dir: Path, graph_summary_data: dict) -> None:
    """
    Generate summary subsets for the Logseq Analyzer.

    Args:
        output_dir (Path): The output directory.
        graph_summary_data (dict): The graph summary data.
    """
    summary_categories = {
        "has_content": {"has_content": True},
        "has_backlinks": {"has_backlinks": True},
        "has_external_links": {"has_external_links": True},
        "has_embedded_links": {"has_embedded_links": True},
        "is_backlinked": {"is_backlinked": True},
        "is_markdown": {"file_extension": ".md"},
        "is_asset": {"file_type": "asset"},
        "is_draw": {"file_type": "draw"},
        "is_journal": {"file_type": "journal"},
        "is_page": {"file_type": "page"},
        "is_whiteboard": {"file_type": "whiteboard"},
        "is_other": {"file_type": "other"},
        "is_orphan_true": {"node_type": "orphan_true"},
        "is_orphan_graph": {"node_type": "orphan_graph"},
        "is_node_root": {"node_type": "root"},
        "is_node_leaf": {"node_type": "leaf"},
        "is_node_branch": {"node_type": "branch"},
    }

    summary_data_subsets = {}
    for output_name, criteria in summary_categories.items():
        summary_subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = summary_subset
        write_output(output_dir, output_name, summary_subset, config.OUTPUT_DIR_SUMMARY)

    return summary_data_subsets


def write_initial_outputs(
    args,
    output_dir,
    meta_alphanum_dictionary,
    meta_dangling_links,
    meta_graph_content,
    graph_meta_data,
    graph_content_data,
    graph_summary_data,
) -> None:
    """Write initial outputs for graph analysis to specified directories.

    Args:
        args: Arguments containing write_graph flag
        output_dir (str): Base directory for output files
        graph_meta_data (dict): Metadata about the graph structure
        meta_graph_content (dict): Content of the graph metadata
        graph_content_data (dict): Content data for graph nodes
        meta_alphanum_dictionary (dict): Dictionary of alphanumeric metadata
        meta_dangling_links (list): List of dangling links in the graph
        graph_summary_data (dict): Summary statistics of the graph

    Returns:
        None

    Writes multiple output files to specified subdirectories under output_dir:
    - alphanum_dictionary and dangling_links to meta subdirectory
    - content_data, meta_data and summary_data to graph subdirectory
    - Optionally writes graph_content to meta subdirectory if args.write_graph is True
    """
    write_output(output_dir, "alphanum_dictionary", meta_alphanum_dictionary, config.OUTPUT_DIR_META)
    write_output(output_dir, "dangling_links", meta_dangling_links, config.OUTPUT_DIR_META)
    write_output(output_dir, "01_meta_data", graph_meta_data, config.OUTPUT_DIR_GRAPH)
    write_output(output_dir, "02_content_data", graph_content_data, config.OUTPUT_DIR_GRAPH)
    write_output(output_dir, "03_summary_data", graph_summary_data, config.OUTPUT_DIR_GRAPH)
    if args.write_graph:
        write_output(output_dir, "graph_content", meta_graph_content, config.OUTPUT_DIR_META)


def core_data_analysis(patterns: Dict[str, Pattern], graph_meta_data: dict, meta_graph_content: dict) -> Tuple[dict, dict, dict, dict]:
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


def process_graph_files(logseq_graph_folder: Path, patterns: Dict[str, Pattern], target_dirs: List[str]) -> Tuple[dict, dict]:
    """
    Process all files in the Logseq graph folder.

    Args:
        logseq_graph_folder (Path): The path to the Logseq graph folder.
        patterns (dict): The compiled regex patterns.
        target_dirs (List[str]): The target directories to process.

    Returns:
        Tuple[dict, dict]: The graph metadata and content data.
    """
    graph_meta_data = {}
    meta_graph_content = {}
    graph_dir_structure = iter_files(logseq_graph_folder, target_dirs)
    for file_path in graph_dir_structure:
        meta_data, graph_content = process_single_file(file_path, patterns)
        name = meta_data["name"]
        if name in graph_meta_data:
            name = meta_data["name_secondary"]
        graph_meta_data[name] = meta_data
        meta_graph_content[name] = graph_content
    return graph_meta_data, meta_graph_content


def setup_logging_and_output(args) -> Tuple[Path, Path]:
    """
    Configure logging and output directory for the Logseq Analyzer.

    Args:
        args (argparse.Namespace): The command line arguments.

    Returns:
        Tuple[Path, Path]: The Logseq graph folder and output directory.
    """
    log_file = Path(args.log_file) if args.log_file else Path(config.DEFAULT_LOG_FILE)
    setup_logging(log_file)
    logging.info("Starting Logseq Analyzer.")

    logseq_graph_folder = Path(args.graph_folder)
    output_dir = Path(args.output_folder) if args.output_folder else Path(config.DEFAULT_OUTPUT_DIR)
    setup_output_directory(output_dir)
    return logseq_graph_folder, output_dir


def setup_logseq_analyzer_args() -> argparse.Namespace:
    """
    Setup the command line arguments for the Logseq Analyzer.

    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description="Logseq Analyzer")

    parser.add_argument("-g", "--graph-folder", action="store", help="path to your Logseq graph folder", required=True)

    parser.add_argument("-o", "--output-folder", action="store", help="path to output folder")

    parser.add_argument("-l", "--log-file", action="store", help="path to log file")

    parser.add_argument(
        "-wg",
        "--write-graph",
        action="store_true",
        help="write all graph content to output folder (warning: may result in large file)",
    )

    parser.add_argument(
        "-ma",
        "--move-unlinked-assets",
        action="store_true",
        help='move unlinked assets to "unlinked_assets" folder',
    )

    parser.add_argument(
        "-mb",
        "--move-bak",
        action="store_true",
        help="move bak files to bak folder in output directory",
    )

    parser.add_argument(
        "-mr",
        "--move-recycle",
        action="store_true",
        help="move recycle files to recycle folder in output directory",
    )

    return parser.parse_args()
