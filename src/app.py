import argparse
import logging
from pathlib import Path
from typing import Tuple, Dict, List, Pattern
from src.helpers import iter_files, extract_logseq_config_edn, move_unlinked_assets
from src.compile_re import compile_regex_patterns
from src.setup import setup_logging, setup_output_directory
from src.reporting import write_output
from src.filedata import process_single_file
from src.contentdata import process_content_data
from src.summarydata import process_summary_data, extract_summary_subset
import src.config as config


def run_app():
    """
    Main function to run the Logseq analyzer.

    Initializes logging, output directory, regex patterns, processes files,
    generates summary data, and writes output to files.
    """
    args = setup_logseq_analyzer_args()
    logseq_graph_folder, output_dir = configure_logging_and_output(args)
    patterns = compile_regex_patterns()
    target_dirs = extract_logseq_config_edn(logseq_graph_folder)
    graph_meta_data, meta_graph_content = process_graph_files(logseq_graph_folder, patterns, target_dirs)
    (
        graph_content_data,
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_summary_data,
    ) = core_data_analysis(patterns, graph_meta_data, meta_graph_content)

    write_output(output_dir, "alphanum_dictionary", meta_alphanum_dictionary, config.OUTPUT_DIR_META)
    write_output(output_dir, "dangling_links", meta_dangling_links, config.OUTPUT_DIR_META)
    write_output(output_dir, "content_data", graph_content_data, config.OUTPUT_DIR_GRAPH)
    write_output(output_dir, "meta_data", graph_meta_data, config.OUTPUT_DIR_GRAPH)
    write_output(output_dir, "summary_data", graph_summary_data, config.OUTPUT_DIR_GRAPH)
    if args.write_graph:
        write_output(output_dir, "graph_content", meta_graph_content, config.OUTPUT_DIR_META)

    logging.info("Logseq Analyzer completed.")


def core_data_analysis(patterns: Dict[str, Pattern], graph_meta_data: dict, meta_graph_content: dict) -> Tuple[dict, dict, dict, dict]:
    """
    Process the core data analysis for the Logseq Analyzer.

    Args:
        patterns (dict): The compiled regex patterns.
        graph_meta_data (dict): The graph metadata.
        meta_graph_content (dict): The graph content data.

    Returns:
        Tuple[dict, dict, dict, dict]: The graph content data, alphanum dictionary,
            dangling links, and graph summary data.
    """
    built_in_properties = config.BUILT_IN_PROPERTIES
    graph_content_data, meta_alphanum_dictionary, meta_dangling_links = process_content_data(
        meta_graph_content, patterns, built_in_properties
    )
    graph_summary_data = process_summary_data(graph_meta_data, graph_content_data, meta_alphanum_dictionary)

    return (
        graph_content_data,
        meta_alphanum_dictionary,
        meta_dangling_links,
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


def configure_logging_and_output(args) -> Tuple[Path, Path]:
    """
    Configure logging and output directory for the Logseq Analyzer.

    Args:
        args (argparse.Namespace): The command line arguments.

    Returns:
        Tuple[Path, Path]: The Logseq graph folder and output directory.
    """
    log_file = Path(args.log_file) if args.log_file else Path("___logseq_analyzer___.log")
    setup_logging(log_file)
    logging.info("Starting Logseq Analyzer.")

    logseq_graph_folder = Path(args.graph_folder) if args.graph_folder else Path("C:/Logseq")
    output_dir = Path(args.output_folder) if args.output_folder else Path("output")
    setup_output_directory(output_dir)
    return logseq_graph_folder, output_dir


def setup_logseq_analyzer_args() -> argparse.Namespace:
    """
    Setup the command line arguments for the Logseq Analyzer.

    Returns:
        argparse.Namespace: The command line arguments.
    """
    parser = argparse.ArgumentParser(description="Logseq Analyzer")
    parser.add_argument("-g", "--graph-folder", type=str, help="Path to the Logseq graph folder")
    parser.add_argument("-o", "--output-folder", type=str, help="Path to the output folder")
    parser.add_argument("-l", "--log-file", type=str, help="Path to the log file")
    parser.add_argument(
        "-ma",
        "--move-unlinked-assets",
        action="store_true",
        help='Move unlinked assets to "unlinked_assets" folder',
    )
    parser.add_argument(
        "-wg",
        "--write-graph",
        action="store_true",
        help="Write all graph content to output folder (large)",
    )
    return parser.parse_args()
