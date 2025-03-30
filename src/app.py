"""
This module contains the main application logic for the Logseq analyzer.
"""

from ._global_objects import ANALYZER, CONFIG, CACHE, GRAPH
from .core import core_data_analysis, process_graph_files
from .logseq_assets import handle_assets
from .logseq_journals import extract_journals_from_dangling_links, process_journals_timelines
from .logseq_move_files import handle_move_files, handle_move_directory
from .process_namespaces import process_namespace_data
from .process_summary_data import generate_sorted_summary_all, generate_summary_subsets


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    def __init__(self):
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, phase, percentage):
        """Simulate updating progress in a GUI."""
        print(f"Phase: {phase}, Progress: {percentage}%")


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    # Get GUI instance if available
    gui_instance = GUIInstanceDummy()
    if kwargs.get("gui_instance"):
        gui_instance = kwargs["gui_instance"]

    gui_instance.update_progress("setup", 20)

    # Parse command line arguments or GUI arguments
    ANALYZER.get_logseq_analyzer_args(**kwargs)
    GRAPH.initialize_graph(ANALYZER.args)
    GRAPH.initialize_config(ANALYZER.args)

    if ANALYZER.args.graph_cache:
        CACHE.clear()

    # Set the configuration for the Logseq graph
    CONFIG.set("ANALYZER", "REPORT_FORMAT", ANALYZER.args.report_format)
    CONFIG.set("CONSTANTS", "GRAPH_DIR", str(GRAPH.directory))
    CONFIG.set_logseq_config_edn_data(GRAPH.logseq_config)

    gui_instance.update_progress("setup", 100)
    gui_instance.update_progress("process_files", 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Check for deleted files and remove them from the database
    CACHE.clear_deleted_files()

    # Process for only modified/new graph files
    graph_data_db = CACHE.get("___meta___graph_data", {})
    graph_content_db = CACHE.get("___meta___graph_content", {})
    graph_meta_data, graph_content_bullets = process_graph_files()
    graph_data_db.update(graph_meta_data)
    graph_content_db.update(graph_content_bullets)

    # Core data analysis
    (
        alphanum_dict,
        alphanum_dict_ns,
        dangling_links,
        graph_data,
        all_refs,
    ) = core_data_analysis(graph_data_db)

    # Namespaces analysis
    summary_namespaces = process_namespace_data(graph_data, dangling_links)

    gui_instance.update_progress("process_files", 100)
    gui_instance.update_progress("summary", 20)

    #################################################################
    # Phase 03: Process summaries
    #################################################################
    # Generate summary
    summary_data_subsets = generate_summary_subsets(graph_data)
    summary_sorted_all = generate_sorted_summary_all(graph_data)

    # TODO Process journal keys to create a timeline
    journals_dangling = extract_journals_from_dangling_links(dangling_links)
    process_journals_timelines(summary_data_subsets["___is_journal"], journals_dangling)

    gui_instance.update_progress("summary", 100)
    gui_instance.update_progress("move_files", 20)

    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    assets_backlinked, assets_not_backlinked = handle_assets(graph_data, summary_data_subsets)
    moved_files = {
        "moved_assets": handle_move_files(
            ANALYZER.args.move_unlinked_assets, graph_data, assets_not_backlinked, ANALYZER.delete_dir
        ),
        "moved_bak": handle_move_directory(
            ANALYZER.args.move_bak, GRAPH.bak_dir, ANALYZER.delete_dir, CONFIG.get("LOGSEQ_FILESYSTEM", "BAK_DIR")
        ),
        "moved_recycle": handle_move_directory(
            ANALYZER.args.move_recycle,
            GRAPH.recycle_dir,
            ANALYZER.delete_dir,
            CONFIG.get("LOGSEQ_FILESYSTEM", "RECYCLE_DIR"),
        ),
    }

    gui_instance.update_progress("move_files", 100)

    #####################################################################
    # Phase 05: Outputs
    #####################################################################
    # Output writing
    output_data = []
    output_dir_meta = CONFIG.get("OUTPUT_DIRS", "META")
    output_data.append(("___meta___alphanum_dict", alphanum_dict, output_dir_meta))
    output_data.append(("___meta___alphanum_dict_ns", alphanum_dict_ns, output_dir_meta))
    output_data.append(("___meta___config_edn_data", GRAPH.logseq_config, output_dir_meta))
    output_data.append(("___meta___graph_data", graph_data, output_dir_meta))
    output_data.append(("all_refs", all_refs, output_dir_meta))
    output_data.append(("dangling_links", dangling_links, output_dir_meta))

    output_dir_summary = CONFIG.get("OUTPUT_DIRS", "SUMMARY")
    for name, data in summary_data_subsets.items():
        output_data.append((name, data, output_dir_summary))

    for name, data in summary_sorted_all.items():
        output_data.append((name, data, output_dir_summary))

    output_dir_namespace = CONFIG.get("OUTPUT_DIRS", "NAMESPACE")
    for name, data in summary_namespaces.items():
        output_data.append((name, data, output_dir_namespace))

    output_dir_assets = CONFIG.get("OUTPUT_DIRS", "ASSETS")
    output_data.append(("moved_files", moved_files, output_dir_assets))
    output_data.append(("assets_backlinked", assets_backlinked, output_dir_assets))
    output_data.append(("assets_not_backlinked", assets_not_backlinked, output_dir_assets))

    if ANALYZER.args.write_graph:
        output_data.append(("___meta___graph_content", graph_content_db, output_dir_meta))

    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        "___meta___alphanum_dict_ns": alphanum_dict_ns,
        "___meta___alphanum_dict": alphanum_dict,
        "___meta___config_edn_data": GRAPH.logseq_config,
        "___meta___graph_content": graph_content_db,
        "___meta___graph_data": graph_data,
        "all_refs": all_refs,
        "dangling_links": dangling_links,
        # General summary
        **summary_data_subsets,
        **summary_sorted_all,
        # Namespaces summary
        **summary_namespaces,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
    }

    CACHE.update(shelve_output_data)
    CACHE.close()

    # TODO write config to file
    with open("user_config.ini", "w", encoding="utf-8") as config_file:
        CONFIG.write(config_file)

    return output_data
