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
    parser.add_argument(
        "-wg",
        "--write-graph",
        action="store_true",
        help="Write all graph content to output folder (large)",
    )
    args = parser.parse_args()

    log_file = (
        Path(args.log_file) if args.log_file else Path("___logseq_analyzer___.log")
    )
    create_logging(log_file)
    logging.info("Starting Logseq Analyzer.")

    logseq_graph_folder = (
        Path(args.graph_folder) if args.graph_folder else Path("C:/Logseq")
    )
    output_dir = Path(args.output_folder) if args.output_folder else Path("output")
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
    write_output(output_dir, "content_data", graph_content_data, graph_subfolder)
    write_output(output_dir, "meta_data", graph_meta_data, graph_subfolder)
    write_output(output_dir, "summary_data", graph_summary_data, graph_subfolder)
    if args.write_graph:
        write_output(output_dir, "graph_content", meta_graph_content, meta_subfolder)

    # Summary Data
    summary_categories = {
        "has_content": {"has_content": True},
        "has_backlinks": {"has_backlinks": True},
        "has_external_links": {"has_external_links": True},
        "has_embedded_links": {"has_embedded_links": True},
        "is_markdown": {"is_markdown": True},
        "is_backlinked": {"is_backlinked": True},
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
        graph_summary_data, file_type="asset", is_backlinked=True
    )
    summary_is_asset_not_backlinked = extract_summary_subset(
        graph_summary_data, file_type="asset", is_backlinked=False
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
    write_output(output_dir, "is_draw", summary_is_draw, summary_subfolder)

    # TODO Global summaries
    test_folder = "test"
    asset_folder = logseq_graph_folder / logseq_config.ASSETS_DIRECTORY
    assets_with_folders = {}
    for root, folders, filenames in Path.walk(asset_folder):
        if filenames and root != asset_folder:
            assets_with_folders.setdefault(root, {})
            assets_with_folders[root]["filenames"] = filenames

    for key in assets_with_folders:
        look_for = f"hls__{key.stem}".lower()
        if look_for in summary_data_subsets["is_page"]:
            assets_with_folders[key]["has_page"] = True
            assets_with_folders[key]["associated_page"] = look_for
        else:
            print(
                f"not found {look_for} in assets_with_folders has {len(assets_with_folders[key])} assets"
            )
    write_output(output_dir, "assets_with_folders", assets_with_folders, test_folder)

    count_has_content = len(summary_data_subsets["has_content"])
    count_has_embedded_links = len(summary_data_subsets["has_embedded_links"])
    count_has_external_links = len(summary_data_subsets["has_external_links"])
    count_has_links = len(summary_data_subsets["has_backlinks"])

    count_is_asset = len(summary_data_subsets["is_asset"])
    count_is_asset_backlinked = len(summary_is_asset_backlinked)
    count_is_asset_not_backlinked = len(summary_is_asset_not_backlinked)
    count_is_backlinked = len(summary_data_subsets["is_backlinked"])
    count_is_draw = len(summary_data_subsets["is_draw"])
    count_is_journals = len(summary_data_subsets["is_journal"])
    count_is_markdown = len(summary_data_subsets["is_markdown"])
    count_is_node_root = len(summary_data_subsets["is_node_root"])
    count_is_node_leaf = len(summary_data_subsets["is_node_leaf"])
    count_is_node_branch = len(summary_data_subsets["is_node_branch"])
    count_is_orphan_true = len(summary_data_subsets["is_orphan_true"])
    count_is_orphan_graph = len(summary_data_subsets["is_orphan_graph"])
    count_is_pages = len(summary_data_subsets["is_page"])
    count_is_whiteboards = len(summary_data_subsets["is_whiteboard"])

    total_pages = count_is_pages + count_is_journals
    percentage_journals = round(count_is_journals / total_pages, 2) * 100
    percentage_pages = round(count_is_pages / total_pages, 2) * 100

    unique_subsets = {
        "unique_page_references": set(),
        "unique_tags": set(),
        "unique_tagged_backlinks": set(),
        "unique_properties": set(),
        "unique_external_links": set(),
        "unique_embedded_links": set(),
    }

    for name, content_data in graph_content_data.items():
        unique_subsets["unique_page_references"].update(content_data["page_references"])
        unique_subsets["unique_tags"].update(content_data["tags"])
        unique_subsets["unique_tagged_backlinks"].update(
            content_data["tagged_backlinks"]
        )
        unique_subsets["unique_properties"].update(content_data["properties"])
        unique_subsets["unique_external_links"].update(content_data["external_links"])
        unique_subsets["unique_embedded_links"].update(content_data["embedded_links"])

    for key in unique_subsets:
        write_output(output_dir, key, unique_subsets[key], test_folder)

    global_summary_data = [
        f"unique_page_references: {len(unique_subsets["unique_page_references"])}",
        f"unique_tags: {len(unique_subsets["unique_tags"])}",
        f"unique_tagged_backlinks: {len(unique_subsets["unique_tagged_backlinks"])}",
        f"unique_properties: {len(unique_subsets["unique_properties"])}",
        f"unique_external_links: {len(unique_subsets["unique_external_links"])}",
        f"unique_embedded_links: {len(unique_subsets["unique_embedded_links"])}",
        f"count_is_markdown: {count_is_markdown}",
        f"total_pages: {total_pages}",
        f"count_is_pages: {count_is_pages}",
        f"count_is_journals: {count_is_journals}",
        f"percentage_pages: {percentage_pages}",
        f"percentage_journals: {percentage_journals}",
        f"count_has_content: {count_has_content}",
        f"count_has_links: {count_has_links}",
        f"count_has_external_links: {count_has_external_links}",
        f"count_has_embedded_links: {count_has_embedded_links}",
        f"count_is_backlinked: {count_is_backlinked}",
        f"count_is_orphan_true: {count_is_orphan_true}",
        f"count_is_orphan_graph: {count_is_orphan_graph}",
        f"count_is_node_root: {count_is_node_root}",
        f"count_is_node_leaf: {count_is_node_leaf}",
        f"count_is_node_branch: {count_is_node_branch}",
        f"count_is_asset: {count_is_asset}",
        f"count_is_asset_backlinked: {count_is_asset_backlinked}",
        f"count_is_asset_not_backlinked: {count_is_asset_not_backlinked}",
        f"count_is_draw: {count_is_draw}",
        f"count_is_whiteboards: {count_is_whiteboards}",
    ]
    write_output(output_dir, "global_summary_data", global_summary_data, test_folder)

    logging.info("Logseq Analyzer completed.")
