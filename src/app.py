import argparse
import logging
import re
from pathlib import Path
from typing import Tuple, Dict, List, Pattern, Set
from src.helpers import iter_files, move_unlinked_assets, move_all_folder_content, is_path_exists
from src.compile_regex import compile_re_content, compile_re_config
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
    # Setup command line arguments
    args = setup_logseq_analyzer_args()

    # Setup logging and output directory
    logseq_graph_folder, output_dir = setup_logging_and_output(args)

    # Extract Logseq configuration and directories
    target_dirs = extract_logseq_config_edn(logseq_graph_folder)

    # Extract bak and recycle folders
    recycle, bak = extract_logseq_bak_recycle(logseq_graph_folder)

    # Compile regex patterns
    patterns = compile_re_content()

    # Process graph files
    graph_meta_data, meta_graph_content = process_graph_files(logseq_graph_folder, patterns, target_dirs)

    # Core data analysis
    (
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_content_data,
        graph_summary_data,
    ) = core_data_analysis(patterns, graph_meta_data, meta_graph_content)

    # Write initial outputs
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

    # Generate summary subsets
    summary_data_subsets = generate_summary_subsets(output_dir, graph_summary_data)

    # Handle assets
    handle_assets(args, output_dir, graph_meta_data, graph_content_data, graph_summary_data, summary_data_subsets)

    # Handle bak and recycle files
    handle_bak_recycle(args, bak, recycle)

    logging.info("Logseq Analyzer completed.")


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


def extract_logseq_config_edn(folder_path: Path) -> Set[str]:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Set[str]: A set of target directories.
    """
    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    config_edn_file = logseq_folder / config.DEFAULT_CONFIG_FILE
    folders = [folder_path, logseq_folder, config_edn_file]
    for folder in folders:
        if not is_path_exists(folder):
            return {}

    config_edn_data = {
        "journal_page_title_format": "MMM do, yyyy",
        "journal_file_name_format": "yyyy_MM_dd",
        "feature_enable_journals": "true",
        "feature_enable_whiteboards": "true",
        "pages_directory": "pages",
        "journals_directory": "journals",
        "whiteboards_directory": "whiteboards",
        "file_name_format": "",
    }

    config_patterns = compile_re_config()

    with config_edn_file.open("r", encoding="utf-8") as f:
        config_edn_content = f.read()
        config_edn_data["journal_page_title_format"] = config_patterns["journal_page_title_pattern"].search(config_edn_content).group(1)
        config_edn_data["journal_file_name_format"] = config_patterns["journal_file_name_pattern"].search(config_edn_content).group(1)
        config_edn_data["feature_enable_journals"] = config_patterns["feature_enable_journals_pattern"].search(config_edn_content).group(1)
        config_edn_data["feature_enable_whiteboards"] = config_patterns["feature_enable_whiteboards_pattern"].search(config_edn_content).group(1)
        config_edn_data["pages_directory"] = config_patterns["pages_directory_pattern"].search(config_edn_content).group(1)
        config_edn_data["journals_directory"] = config_patterns["journals_directory_pattern"].search(config_edn_content).group(1)
        config_edn_data["whiteboards_directory"] = config_patterns["whiteboards_directory_pattern"].search(config_edn_content).group(1)
        config_edn_data["file_name_format"] = config_patterns["file_name_format_pattern"].search(config_edn_content).group(1)
        
    config.JOURNAL_PAGE_TITLE_FORMAT = config_edn_data["journal_page_title_format"]
    config.JOURNAL_FILE_NAME_FORMAT = config_edn_data["journal_file_name_format"]
    config.NAMESPACE_FORMAT = config_edn_data["file_name_format"]
    if config.NAMESPACE_FORMAT == ":triple-lowbar":
        config.NAMESPACE_FILE_SEP = "___"
    config.PAGES = config_edn_data["pages_directory"]
    config.JOURNALS = config_edn_data["journals_directory"]
    config.WHITEBOARDS = config_edn_data["whiteboards_directory"]
    target_dirs = {
        config.ASSETS,
        config.DRAWS,
        config.JOURNALS,
        config.PAGES,
        config.WHITEBOARDS,
    }
    return target_dirs


def extract_logseq_bak_recycle(folder_path: Path) -> Tuple[Path, Path]:
    """
    Extract bak and recycle data from a Logseq.

    Args:
        folder_path (Path): The path to the Logseq graph folder.

    Returns:
        Tuple[Path, Path]: A tuple containing the bak and recycle folders.
    """
    logseq_folder = folder_path / config.DEFAULT_LOGSEQ_DIR
    folders = [folder_path, logseq_folder]
    for folder in folders:
        if not is_path_exists(folder):
            return ()

    recycling_folder = logseq_folder / config.DEFAULT_RECYCLE_DIR
    bak_folder = logseq_folder / config.DEFAULT_BAK_DIR

    for folder in [recycling_folder, bak_folder]:
        if not is_path_exists(folder):
            return ()

    return recycling_folder, bak_folder


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
