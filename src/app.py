import argparse
import logging
from pathlib import Path

from src.helpers import iter_files, extract_logseq_config_edn, move_unlinked_assets
from src.compile_re import compile_regex_patterns
from src.create import create_logging, create_output_directory
from src.reporting import write_output
from src.filedata import process_single_file
from src.contentdata import process_content_data
from src.summarydata import process_summary_data, extract_summary_subset
import src.logseq_config as logseq_config


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
