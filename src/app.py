"""
This module contains the main application logic for the Logseq analyzer.
"""

from .cache import Cache
from .config_loader import Config
from .core import core_data_analysis, process_graph_files
from .logseq_analyzer import LogseqAnalyzer
from .logseq_assets import handle_assets
from .logseq_graph import LogseqGraph
from .logseq_journals import extract_journals_from_dangling_links, process_journals_timelines
from .logseq_move_files import handle_move_files, handle_move_directory
from .process_namespaces import process_namespace_data
from .process_summary_data import generate_sorted_summary_all, generate_summary_subsets


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    # Get GUI instance if available
    gui_instance = kwargs.get("gui_instance")
    if gui_instance:
        gui_instance.update_progress("setup", 20)

    # Parse command line arguments or GUI arguments
    analyzer = LogseqAnalyzer.get_instance()
    analyzer.get_logseq_analyzer_args(**kwargs)
    config = Config.get_instance()
    cache = Cache.get_instance(config.get("CONSTANTS", "CACHE"))
    graph = LogseqGraph.get_instance(analyzer.args)
    if analyzer.args.graph_cache:
        cache.clear()

    # Set the configuration for the Logseq graph
    config.set("ANALYZER", "REPORT_FORMAT", analyzer.args.report_format)
    config.set("CONSTANTS", "GRAPH_DIR", str(graph.directory))
    config.set_logseq_config_edn_data(graph.logseq_config)

    if gui_instance:
        gui_instance.update_progress("setup", 100)
        gui_instance.update_progress("process_files", 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Check for deleted files and remove them from the database
    cache.clear_deleted_files()

    # Process for only modified/new graph files
    graph_data_db = cache.get("___meta___graph_data", {})
    graph_content_db = cache.get("___meta___graph_content", {})
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

    if gui_instance:
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

    if gui_instance:
        gui_instance.update_progress("summary", 100)
        gui_instance.update_progress("move_files", 20)

    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    assets_backlinked, assets_not_backlinked = handle_assets(graph_data, summary_data_subsets)

    moved_files = {}
    moved_files["moved_assets"] = handle_move_files(
        analyzer.args.move_unlinked_assets, graph_data, assets_not_backlinked, analyzer.delete_dir
    )
    moved_files["moved_bak"] = handle_move_directory(
        analyzer.args.move_bak, graph.bak_dir, analyzer.delete_dir, config.get("LOGSEQ_FILESYSTEM", "BAK_DIR")
    )
    moved_files["moved_recycle"] = handle_move_directory(
        analyzer.args.move_recycle,
        graph.recycle_dir,
        analyzer.delete_dir,
        config.get("LOGSEQ_FILESYSTEM", "RECYCLE_DIR"),
    )

    if gui_instance:
        gui_instance.update_progress("move_files", 100)

    #####################################################################
    # Phase 05: Outputs
    #####################################################################
    # Output writing
    output_data = []
    output_dir_meta = config.get("OUTPUT_DIRS", "META")
    output_data.append(("___meta___alphanum_dict", alphanum_dict, output_dir_meta))
    output_data.append(("___meta___alphanum_dict_ns", alphanum_dict_ns, output_dir_meta))
    output_data.append(("___meta___config_edn_data", graph.logseq_config, output_dir_meta))
    output_data.append(("___meta___graph_data", graph_data, output_dir_meta))
    output_data.append(("all_refs", all_refs, output_dir_meta))
    output_data.append(("dangling_links", dangling_links, output_dir_meta))

    output_dir_summary = config.get("OUTPUT_DIRS", "SUMMARY")
    for name, data in summary_data_subsets.items():
        output_data.append((name, data, output_dir_summary))

    for name, data in summary_sorted_all.items():
        output_data.append((name, data, output_dir_summary))

    output_dir_namespace = config.get("OUTPUT_DIRS", "NAMESPACE")
    for name, data in summary_namespaces.items():
        output_data.append((name, data, output_dir_namespace))

    output_dir_assets = config.get("OUTPUT_DIRS", "ASSETS")
    output_data.append(("moved_files", moved_files, output_dir_assets))
    output_data.append(("assets_backlinked", assets_backlinked, output_dir_assets))
    output_data.append(("assets_not_backlinked", assets_not_backlinked, output_dir_assets))

    if analyzer.args.write_graph:
        output_data.append(("___meta___graph_content", graph_content_db, output_dir_meta))

    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        "___meta___alphanum_dict_ns": alphanum_dict_ns,
        "___meta___alphanum_dict": alphanum_dict,
        "___meta___config_edn_data": graph.logseq_config,
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

    cache.update(shelve_output_data)
    cache.close()

    # TODO write config to file
    with open("user_config.ini", "w", encoding="utf-8") as config_file:
        config.write(config_file)

    return output_data
