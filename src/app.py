import argparse
import logging
import re
from datetime import datetime
from pathlib import Path
import shutil
from typing import Optional, Dict, Any, Pattern, Generator, Set, Tuple

from src.compile_re import compile_regex_patterns
from src.create import create_logging, create_output_directory
from src.reporting import write_output
from src.filedata import process_single_file
from src.contentdata import process_content_data
from src.summarydata import process_summary_data, extract_summary_subset
import src.logseq_config as logseq_config


def iter_files(
    directory: Path, target_dirs: Optional[Set[str]] = None
) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the given directory.

    If target_dirs is provided, only yield files that reside within directories
    whose names are in the target_dirs set.

    Args:
        directory (Path): The root directory to search.
        target_dirs (Optional[Set[str]]): Set of allowed parent directory names.

    Yields:
        Path: File paths that match the criteria.
    """
    if not directory.is_dir():
        logging.error(f"Directory not found: {directory}")
        return

    for path in directory.rglob("*"):
        if path.is_file():
            if target_dirs:
                if path.parent.name in target_dirs:
                    yield path
                else:
                    logging.info(f"Skipping file {path} outside target directories")
            else:
                yield path


def extract_logseq_config_edn(file_path: Path) -> Set[str]:
    """
    Extract EDN configuration data from a Logseq configuration file.

    Args:
        file_path (Path): The path to the Logseq graph folder.

    Returns:
        Set[str]: A set of target directories.
    """
    if not file_path.is_dir():
        logging.error(f"Directory not found: {file_path}")
        return {}

    logseq_folder = file_path / "logseq"
    if not logseq_folder.is_dir():
        logging.error(f"Directory not found: {logseq_folder}")
        return {}

    config_edn_file = logseq_folder / "config.edn"
    if not config_edn_file.is_file():
        logging.error(f"File not found: {config_edn_file}")
        return {}

    journal_page_title_pattern = re.compile(r':journal/page-title-format\s+"([^"]+)"')
    journal_file_name_pattern = re.compile(r':journal/file-name-format\s+"([^"]+)"')
    feature_enable_journals_pattern = re.compile(
        r":feature/enable-journals\?\s+(true|false)"
    )
    feature_enable_whiteboards_pattern = re.compile(
        r":feature/enable-whiteboards\?\s+(true|false)"
    )
    pages_directory_pattern = re.compile(r':pages-directory\s+"([^"]+)"')
    journals_directory_pattern = re.compile(r':journals-directory\s+"([^"]+)"')
    whiteboards_directory_pattern = re.compile(r':whiteboards-directory\s+"([^"]+)"')
    file_name_format_pattern = re.compile(r":file/name-format\s+(.+)")

    config_edn_data = {
        "journal_page_title_format": "MMM do, yyyy",
        "journal_file_name_format": "yyyy_MM_dd",
        "feature_enable_journals": "true",
        "feature_enable_whiteboards": "true",
        "pages_directory": "pages",
        "journals_directory": "journals",
        "whiteboards_directory": "whiteboards",
        "file_name_format": ":triple-lowbar",
    }

    with config_edn_file.open("r", encoding="utf-8") as f:
        config_edn_content = f.read()
        config_edn_data["journal_page_title_format"] = (
            journal_page_title_pattern.search(config_edn_content).group(1)
        )
        config_edn_data["journal_file_name_format"] = journal_file_name_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["feature_enable_journals"] = (
            feature_enable_journals_pattern.search(config_edn_content).group(1)
        )
        config_edn_data["feature_enable_whiteboards"] = (
            feature_enable_whiteboards_pattern.search(config_edn_content).group(1)
        )
        config_edn_data["pages_directory"] = pages_directory_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["journals_directory"] = journals_directory_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["whiteboards_directory"] = whiteboards_directory_pattern.search(
            config_edn_content
        ).group(1)
        config_edn_data["file_name_format"] = file_name_format_pattern.search(
            config_edn_content
        ).group(1)

    setattr(
        logseq_config,
        "JOURNAL_PAGE_TITLE_FORMAT",
        config_edn_data["journal_page_title_format"],
    )
    setattr(
        logseq_config,
        "JOURNAL_FILE_NAME_FORMAT",
        config_edn_data["journal_file_name_format"],
    )
    setattr(logseq_config, "PAGES_DIRECTORY", config_edn_data["pages_directory"])
    setattr(logseq_config, "JOURNALS_DIRECTORY", config_edn_data["journals_directory"])
    setattr(
        logseq_config, "WHITEBOARDS_DIRECTORY", config_edn_data["whiteboards_directory"]
    )
    target_dirs = {
        logseq_config.ASSETS_DIRECTORY,
        logseq_config.DRAWS_DIRECTORY,
        logseq_config.JOURNALS_DIRECTORY,
        logseq_config.PAGES_DIRECTORY,
        logseq_config.WHITEBOARDS_DIRECTORY,
    }
    return target_dirs


def move_unlinked_assets(
    summary_is_asset_not_backlinked: Dict[str, Any], graph_meta_data: Dict[str, Any]
) -> None:
    """
    Move unlinked assets to a separate directory.

    Args:
        summary_is_asset_not_backlinked (Dict[str, Any]): Summary data for unlinked assets.
        graph_meta_data (Dict[str, Any]): Metadata for each file.
    """
    unlinked_assets_dir = Path("unlinked_assets")
    if not unlinked_assets_dir.exists():
        unlinked_assets_dir.mkdir()
        logging.info(f"Created directory: {unlinked_assets_dir}")

    for name in summary_is_asset_not_backlinked.keys():
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = unlinked_assets_dir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.info(f"Moved unlinked asset: {file_path} to {new_path}")
        except Exception as e:
            logging.error(
                f"Failed to move unlinked asset: {file_path} to {new_path}: {e}"
            )


def run_app():
    """
    Main function to run the Logseq analyzer.

    Initializes logging, output directory, regex patterns, processes files,
    generates summary data, and writes output to files.
    """
    parser = argparse.ArgumentParser(description="Logseq Analyzer")
    parser.add_argument(
        "-g", "--graph-folder", type=str, help="Path to the Logseq graph folder"
    )
    parser.add_argument(
        "-o", "--output-folder", type=str, help="Path to the output folder"
    )
    parser.add_argument("-l", "--log-file", type=str, help="Path to the log file")
    parser.add_argument(
        "-ma",
        "--move-unlinked-assets",
        action="store_true",
        help='Move unlinked assets to "unlinked_assets" folder',
    )
    args = parser.parse_args()

    logseq_graph_folder = (
        Path(args.graph_folder) if args.graph_folder else Path("C:/Logseq")
    )
    output_dir = Path(args.output_folder) if args.output_folder else Path("output")
    log_file = (
        Path(args.log_file) if args.log_file else Path("___logseq_analyzer___.log")
    )

    create_logging(log_file)
    logging.info("Starting Logseq Analyzer.")
    create_output_directory(output_dir)
    patterns = compile_regex_patterns()

    # Extract Logseq configuration data
    target_dirs = extract_logseq_config_edn(logseq_graph_folder)

    # Outputs
    meta_alphanum_dictionary = {}
    meta_graph_content = {}
    graph_meta_data = {}
    graph_content_data = {}
    graph_summary_data = {}

    for file_path in iter_files(logseq_graph_folder, target_dirs):
        meta_data, graph_content = process_single_file(file_path, patterns)
        name = meta_data["name"]
        if name in graph_meta_data:
            name = meta_data["name_secondary"]
        graph_meta_data[name] = meta_data
        meta_graph_content[name] = graph_content

    built_in_properties = logseq_config.BUILT_IN_PROPERTIES
    graph_content_data, meta_alphanum_dictionary, meta_dangling_links = (
        process_content_data(meta_graph_content, patterns, built_in_properties)
    )
    graph_summary_data = process_summary_data(
        graph_meta_data, graph_content_data, meta_alphanum_dictionary
    )

    meta_subfolder = "__meta"
    graph_subfolder = "graph"
    summary_subfolder = "summary"

    write_output(
        output_dir, "alphanum_dictionary", meta_alphanum_dictionary, meta_subfolder
    )
    write_output(output_dir, "dangling_links", meta_dangling_links, meta_subfolder)
    write_output(output_dir, "graph_content", meta_graph_content, meta_subfolder)
    write_output(output_dir, "content_data", graph_content_data, graph_subfolder)
    write_output(output_dir, "meta_data", graph_meta_data, graph_subfolder)
    write_output(output_dir, "summary_data", graph_summary_data, graph_subfolder)

    summary_categories = {
        "has_content": {"has_content": True},
        "has_links": {"has_links": True},
        "has_external_links": {"has_external_links": True},
        "has_embedded_links": {"has_embedded_links": True},
        "is_markdown": {"is_markdown": True},
        "is_asset": {"is_asset": True},
        "is_draw": {"is_draw": True},
        "is_journal": {"is_journal": True},
        "is_page": {"is_page": True},
        "is_whiteboard": {"is_whiteboard": True},
        "is_other": {"is_other": True},
        "is_backlinked": {"is_backlinked": True},
        "is_orphan_true": {"is_orphan_true": True},
        "is_orphan_graph": {"is_orphan_graph": True},
        "is_node_root": {"is_node_root": True},
        "is_node_leaf": {"is_node_leaf": True},
        "is_node_branch": {"is_node_branch": True},
    }

    summary_data_subsets = {}
    for output_name, criteria in summary_categories.items():
        summary_subset = extract_summary_subset(graph_summary_data, **criteria)
        summary_data_subsets[output_name] = summary_subset
        write_output(output_dir, output_name, summary_subset, summary_subfolder)

    # Asset Handling
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

    summary_is_asset_backlinked = extract_summary_subset(
        graph_summary_data, is_asset=True, is_backlinked=True
    )
    summary_is_asset_not_backlinked = extract_summary_subset(
        graph_summary_data, is_asset=True, is_backlinked=False
    )
    write_output(
        output_dir,
        "is_asset_backlinked",
        summary_is_asset_backlinked,
        summary_subfolder,
    )
    write_output(
        output_dir,
        "is_asset_not_backlinked",
        summary_is_asset_not_backlinked,
        summary_subfolder,
    )

    # Optional move unlinked assets
    if args.move_unlinked_assets:
        move_unlinked_assets(summary_is_asset_not_backlinked, graph_meta_data)

    # Draws Handling
    summary_is_draw = summary_data_subsets["is_draw"]
    for name, content_data in graph_content_data.items():
        if not content_data["draws"]:
            continue
        for draw in content_data["draws"]:
            if draw in summary_is_draw:
                summary_is_draw[draw]["is_backlinked"] = True
    write_output(
        output_dir, "is_draw", summary_is_draw, summary_subfolder
    )  # overwrites
    logging.info("Logseq Analyzer completed.")
