"""
This module contains the main application logic for the Logseq analyzer.
"""

from pathlib import Path

from ._global_objects import ANALYZER, ANALYZER_CONFIG, CACHE, GRAPH_CONFIG, PATTERNS
from .namespace_analyzer import NamespaceAnalyzer
from .report_writer import ReportWriter
from .logseq_graph import LogseqGraph
from .logseq_journals import LogseqJournals
from .logseq_file_mover import LogseqFileMover


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

    # Get GUI instance if available
    gui_instance = kwargs.get("gui_instance", GUIInstanceDummy())
    ###################################################################
    # Phase 01: Setup
    ###################################################################
    gui_instance.update_progress("setup", 20)

    PATTERNS.compile_re_content()
    PATTERNS.compile_re_content_double_curly_brackets()
    PATTERNS.compile_re_content_advanced_command()
    PATTERNS.compile_re_ext_links()
    PATTERNS.compile_re_emb_links()
    PATTERNS.compile_re_code()
    ANALYZER_CONFIG.get_built_in_properties()
    ANALYZER_CONFIG.get_datetime_token_map()
    ANALYZER_CONFIG.get_datetime_token_pattern()
    ANALYZER.get_logseq_analyzer_args(**kwargs)
    ANALYZER.create_output_directory()
    ANALYZER.create_log_file()
    ANALYZER.create_delete_directory()
    GRAPH_CONFIG.initialize_graph()
    GRAPH_CONFIG.initialize_config()
    ANALYZER_CONFIG.set_logseq_config_edn_data(GRAPH_CONFIG, ANALYZER.args.report_format)
    ANALYZER_CONFIG.get_logseq_target_dirs()
    ANALYZER_CONFIG.set_journal_py_formatting()
    CACHE.choose_cache_clear(ANALYZER.args.graph_cache)

    gui_instance.update_progress("setup", 100)
    ################################################################
    # Phase 02: Process files
    ################################################################
    gui_instance.update_progress("process_files", 20)
    # Process for only modified/new graph files
    graph = LogseqGraph()
    graph.process_graph_files()

    graph_data_db = CACHE.get("___meta___graph_data", {})
    graph_data_db.update(graph.data)
    graph.data = graph_data_db

    graph_content_db = CACHE.get("___meta___graph_content", {})
    graph_content_db.update(graph.content_bullets)
    graph.content_bullets = graph_content_db

    graph_hashed_files_db = CACHE.get("graph_hashed_files", {})
    graph_hashed_files_db.update(graph.hashed_files)
    graph.hashed_files = graph_hashed_files_db

    graph_names_to_hashes_db = CACHE.get("graph_names_to_hashes", {})
    graph_names_to_hashes_db.update(graph.names_to_hashes)
    graph.names_to_hashes = graph_names_to_hashes_db

    graph_dangling_links_db = CACHE.get("dangling_links", set())
    graph_dangling_links = {d for d in graph.dangling_links if d not in graph_dangling_links_db}
    graph.dangling_links = graph_dangling_links.union(graph_dangling_links_db)

    graph.post_processing_content()
    graph.process_summary_data()

    graph_ns = NamespaceAnalyzer(graph)
    graph_ns.init_ns_parts()
    graph_ns.analyze_ns_queries()
    graph_ns.detect_non_ns_conflicts()
    graph_ns.detect_parent_depth_conflicts()
    namespace_data = {
        "___meta___namespace_data": graph_ns.namespace_data,
        "___meta___namespace_parts": graph_ns.namespace_parts,
        "unique_namespace_parts": graph_ns.unique_namespace_parts,
        "namespace_details": graph_ns.namespace_details,
        "unique_namespaces_per_level": graph_ns.unique_namespaces_per_level,
        "namespace_queries": graph_ns.namespace_queries,
        "namespace_hierarchy": graph_ns.tree,
        "conflicts_non_namespace": graph_ns.conflicts_non_namespace,
        "conflicts_dangling": graph_ns.conflicts_dangling,
        "conflicts_parent_depth": graph_ns.conflicts_parent_depth,
        "conflicts_parent_unique": graph_ns.conflicts_parent_unique,
    }

    gui_instance.update_progress("process_files", 100)
    #################################################################
    # Phase 03: Process summaries
    #################################################################
    gui_instance.update_progress("summary", 20)
    # Generate summary
    graph.generate_summary_file_subsets()
    graph.generate_summary_data_subsets()

    # Process journal keys to create a timeline
    graph_journals = LogseqJournals(graph)
    graph_journals.process_journals_timelines()

    gui_instance.update_progress("summary", 100)
    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    gui_instance.update_progress("move_files", 20)

    graph.handle_assets()
    logseq_assets_handler = LogseqFileMover(ANALYZER, ANALYZER_CONFIG, GRAPH_CONFIG, graph)

    gui_instance.update_progress("move_files", 100)
    #####################################################################
    # Phase 05: Outputs
    #####################################################################
    # Output writing
    output_dir_meta = ANALYZER_CONFIG.get("OUTPUT_DIRS", "META")
    output_dir_summary = ANALYZER_CONFIG.get("OUTPUT_DIRS", "SUMMARY")
    output_dir_namespace = ANALYZER_CONFIG.get("OUTPUT_DIRS", "NAMESPACE")
    output_dir_assets = ANALYZER_CONFIG.get("OUTPUT_DIRS", "ASSETS")
    journal_dir = ANALYZER_CONFIG.get("OUTPUT_DIRS", "LOGSEQ_JOURNALS")
    # Journals
    ReportWriter("dangling_journals", graph_journals.dangling_journals, journal_dir).write()
    ReportWriter("processed_keys", graph_journals.processed_keys, journal_dir).write()
    ReportWriter("complete_timeline", graph_journals.complete_timeline, journal_dir).write()
    ReportWriter("missing_keys", graph_journals.missing_keys, journal_dir).write()
    ReportWriter("timeline_stats", graph_journals.timeline_stats, journal_dir).write()
    ReportWriter("dangling_journals_past", graph_journals.dangling_journals_past, journal_dir).write()
    ReportWriter("dangling_journals_future", graph_journals.dangling_journals_future, journal_dir).write()
    # Meta
    ReportWriter("___meta___unique_linked_refs", graph.unique_linked_references, output_dir_meta).write()
    ReportWriter(
        "___meta___unique_linked_refs_ns",
        graph.unique_linked_references_ns,
        output_dir_meta,
    ).write()
    ReportWriter("___meta___graph_data", graph.data, output_dir_meta).write()
    ReportWriter("all_refs", graph.all_linked_references, output_dir_meta).write()
    ReportWriter("dangling_links", graph.dangling_links, output_dir_meta).write()
    ReportWriter("graph_hashed_files", graph.hashed_files, output_dir_meta).write()
    ReportWriter("graph_names_to_hashes", graph.names_to_hashes, output_dir_meta).write()
    # Summary
    for name, data in graph.summary_file_subsets.items():
        ReportWriter(name, data, output_dir_summary).write()
    for name, data in graph.summary_data_subsets.items():
        ReportWriter(name, data, "summary_content_data").write()
    # Namespace
    for name, data in namespace_data.items():
        ReportWriter(name, data, output_dir_namespace).write()
    # Move files and assets
    ReportWriter("moved_files", logseq_assets_handler.moved_files, output_dir_assets).write()
    ReportWriter("assets_backlinked", graph.assets_backlinked, output_dir_assets).write()
    ReportWriter("assets_not_backlinked", graph.assets_not_backlinked, output_dir_assets).write()
    if ANALYZER.args.write_graph:
        ReportWriter("___meta___graph_content", graph_content_db, output_dir_meta).write()
    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        "___meta___unique_linked_refs_ns": graph.unique_linked_references_ns,
        "___meta___unique_linked_refs": graph.unique_linked_references,
        "___meta___graph_content": graph_content_db,
        "___meta___graph_data": graph.data,
        "all_refs": graph.all_linked_references,
        "dangling_links": graph.dangling_links,
        # General summary
        **graph.summary_file_subsets,
        **graph.summary_data_subsets,
        # Namespaces summary
        **namespace_data,
        # Move files and assets
        "moved_files": logseq_assets_handler.moved_files,
        "assets_backlinked": graph.assets_backlinked,
        "assets_not_backlinked": graph.assets_not_backlinked,
        # Other
        "graph_hashed_files": graph.hashed_files,
        "graph_names_to_hashes": graph.names_to_hashes,
    }

    CACHE.update(shelve_output_data)
    CACHE.close()

    # Write user config to file
    with open(f"{Path('configuration')}/user_config.ini", "w", encoding="utf-8") as config_file:
        ANALYZER_CONFIG.write(config_file)
