"""
This module contains the main application logic for the Logseq analyzer.
"""

from ._global_objects import ANALYZER, ANALYZER_CONFIG, CACHE, GRAPH_CONFIG, PATTERNS
from .report_writer import ReportWriter
from .logseq_graph import LogseqGraph
from .logseq_assets import handle_assets
from .logseq_journals import extract_journals_from_dangling_links, process_journals_timelines
from .logseq_move_files import handle_move_files, handle_move_directory


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
    gui_instance = kwargs.get("gui_instance", GUIInstanceDummy())
    gui_instance.update_progress("setup", 20)

    PATTERNS.compile_re_content()
    PATTERNS.compile_re_content_double_curly_brackets()
    PATTERNS.compile_re_content_advanced_command()
    PATTERNS.compile_re_config()
    PATTERNS.compile_re_ext_links()
    PATTERNS.compile_re_emb_links()
    PATTERNS.compile_re_code()

    ANALYZER_CONFIG.get_logseq_target_dirs()
    ANALYZER_CONFIG.get_built_in_properties()
    ANALYZER_CONFIG.get_datetime_token_map()
    ANALYZER_CONFIG.get_datetime_token_pattern()

    ANALYZER.get_logseq_analyzer_args(**kwargs)
    ANALYZER.create_output_directory()
    ANALYZER.create_log_file()
    ANALYZER.create_delete_directory()

    GRAPH_CONFIG.initialize_graph(ANALYZER.args)
    GRAPH_CONFIG.initialize_config(ANALYZER.args)

    if ANALYZER.args.graph_cache:
        CACHE.clear()
    else:
        CACHE.clear_deleted_files()

    # Set the configuration for the Logseq graph
    ANALYZER_CONFIG.set("ANALYZER", "REPORT_FORMAT", ANALYZER.args.report_format)
    ANALYZER_CONFIG.set("CONSTANTS", "GRAPH_DIR", str(GRAPH_CONFIG.directory))
    ANALYZER_CONFIG.set_logseq_config_edn_data(GRAPH_CONFIG.logseq_config)

    gui_instance.update_progress("setup", 100)
    gui_instance.update_progress("process_files", 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Process for only modified/new graph files

    graph = LogseqGraph()
    graph.process_graph_files()
    graph_data_db = CACHE.get("___meta___graph_data", {})
    graph_data_db.update(graph.data)
    graph.data = graph_data_db
    graph_content_db = CACHE.get("___meta___graph_content", {})
    graph_content_db.update(graph.content_bullets)
    graph.content_bullets = graph_content_db
    graph.post_processing_content()
    graph.process_summary_data()
    graph.process_namespace_data()

    gui_instance.update_progress("process_files", 100)
    gui_instance.update_progress("summary", 20)

    #################################################################
    # Phase 03: Process summaries
    #################################################################
    # Generate summary
    graph.generate_summary_file_subsets()
    graph.generate_summary_data_subsets()

    # TODO Process journal keys to create a timeline
    journals_dangling = extract_journals_from_dangling_links(graph.dangling_links)
    process_journals_timelines(graph.summary_file_subsets["___is_filetype_journal"], journals_dangling)

    gui_instance.update_progress("summary", 100)
    gui_instance.update_progress("move_files", 20)

    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    assets_backlinked, assets_not_backlinked = handle_assets(graph.data, graph.summary_file_subsets)
    moved_files = {
        "moved_assets": handle_move_files(
            ANALYZER.args.move_unlinked_assets, graph.data, assets_not_backlinked, ANALYZER.delete_dir
        ),
        "moved_bak": handle_move_directory(
            ANALYZER.args.move_bak,
            GRAPH_CONFIG.bak_dir,
            ANALYZER.delete_dir,
            ANALYZER_CONFIG.get("LOGSEQ_FILESYSTEM", "BAK_DIR"),
        ),
        "moved_recycle": handle_move_directory(
            ANALYZER.args.move_recycle,
            GRAPH_CONFIG.recycle_dir,
            ANALYZER.delete_dir,
            ANALYZER_CONFIG.get("LOGSEQ_FILESYSTEM", "RECYCLE_DIR"),
        ),
    }

    gui_instance.update_progress("move_files", 100)

    #####################################################################
    # Phase 05: Outputs
    #####################################################################
    # Output writing
    output_dir_meta = ANALYZER_CONFIG.get("OUTPUT_DIRS", "META")
    output_dir_summary = ANALYZER_CONFIG.get("OUTPUT_DIRS", "SUMMARY")
    output_dir_namespace = ANALYZER_CONFIG.get("OUTPUT_DIRS", "NAMESPACE")
    output_dir_assets = ANALYZER_CONFIG.get("OUTPUT_DIRS", "ASSETS")
    ReportWriter("___meta___alphanum_dict", graph.alphanum_dict, output_dir_meta).write()
    ReportWriter("___meta___alphanum_dict_ns", graph.alphanum_dict_ns, output_dir_meta).write()
    ReportWriter("___meta___graph_data", graph.data, output_dir_meta).write()
    ReportWriter("all_refs", graph.all_linked_references, output_dir_meta).write()
    ReportWriter("dangling_links", graph.dangling_links, output_dir_meta).write()
    ReportWriter("graph_files", graph.files, output_dir_meta).write()

    for name, data in graph.summary_file_subsets.items():
        ReportWriter(name, data, output_dir_summary).write()

    for name, data in graph.summary_data_subsets.items():
        ReportWriter(name, data, "summary_content_data").write()

    for name, data in graph.namespace_data.items():
        ReportWriter(name, data, output_dir_namespace).write()

    ReportWriter("moved_files", moved_files, output_dir_assets).write()
    ReportWriter("assets_backlinked", assets_backlinked, output_dir_assets).write()
    ReportWriter("assets_not_backlinked", assets_not_backlinked, output_dir_assets).write()
    if ANALYZER.args.write_graph:
        ReportWriter("___meta___graph_content", graph_content_db, output_dir_meta).write()

    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        "___meta___alphanum_dict_ns": graph.alphanum_dict_ns,
        "___meta___alphanum_dict": graph.alphanum_dict,
        "___meta___graph_content": graph_content_db,
        "___meta___graph_data": graph.data,
        "all_refs": graph.all_linked_references,
        "dangling_links": graph.dangling_links,
        # General summary
        **graph.summary_file_subsets,
        **graph.summary_data_subsets,
        # Namespaces summary
        **graph.namespace_data,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
        # Other
        "graph_files": graph.files,
    }

    CACHE.update(shelve_output_data)
    CACHE.close()

    # TODO write config to file
    with open("user_config.ini", "w", encoding="utf-8") as config_file:
        ANALYZER_CONFIG.write(config_file)
