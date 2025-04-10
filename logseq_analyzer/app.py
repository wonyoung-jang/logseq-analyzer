"""
This module contains the main application logic for the Logseq analyzer.
"""

from .logseq_namespaces import LogseqNamespaces
from .report_writer import ReportWriter
from .logseq_graph import LogseqGraph
from .logseq_journals import LogseqJournals
from .logseq_file_mover import LogseqFileMover
from .logseq_analyzer_config import ANALYZER_CONFIG
from .logseq_analyzer import ANALYZER
from .logseq_graph_config import GRAPH_CONFIG
from .cache import CACHE
import logging


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    def __init__(self):
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, phase, percentage):
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %s - %d%%", phase, percentage)


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Get GUI instance if available
    gui_instance = kwargs.get("gui_instance", GUIInstanceDummy())
    ###################################################################
    # Phase 01: Setup
    ###################################################################
    gui_instance.update_progress("progress", 10)
    ANALYZER.get_logseq_analyzer_args(**kwargs)
    ANALYZER.create_output_directory()
    ANALYZER.create_log_file()
    ANALYZER.create_delete_directory()
    GRAPH_CONFIG.initialize_graph()
    GRAPH_CONFIG.initialize_config()
    ANALYZER_CONFIG.set_logseq_config_edn_data(GRAPH_CONFIG, ANALYZER.args.report_format)
    ANALYZER_CONFIG.get_logseq_target_dirs()
    ANALYZER_CONFIG.set_journal_py_formatting()
    CACHE.choose_cache_clear()
    gui_instance.update_progress("progress", 20)
    graph = LogseqGraph(CACHE)
    gui_instance.update_progress("progress", 30)
    graph_ns = LogseqNamespaces(graph)
    gui_instance.update_progress("progress", 40)
    journals = LogseqJournals(graph)
    gui_instance.update_progress("progress", 60)
    logseq_assets_handler = LogseqFileMover(ANALYZER, ANALYZER_CONFIG, GRAPH_CONFIG, graph)
    gui_instance.update_progress("progress", 80)
    #####################################################################
    # Phase 05: Outputs
    #####################################################################
    # Output writing
    output_dir_meta = ANALYZER_CONFIG.get("OUTPUT_DIRS", "META")
    output_dir_summary = ANALYZER_CONFIG.get("OUTPUT_DIRS", "SUMMARY")
    output_dir_namespace = ANALYZER_CONFIG.get("OUTPUT_DIRS", "NAMESPACE")
    output_dir_assets = ANALYZER_CONFIG.get("OUTPUT_DIRS", "ASSETS")
    output_dir_journal = ANALYZER_CONFIG.get("OUTPUT_DIRS", "LOGSEQ_JOURNALS")
    # Journals
    ReportWriter("dangling_journals", journals.dangling_journals, output_dir_journal).write()
    ReportWriter("processed_keys", journals.processed_keys, output_dir_journal).write()
    ReportWriter("complete_timeline", journals.complete_timeline, output_dir_journal).write()
    ReportWriter("missing_keys", journals.missing_keys, output_dir_journal).write()
    ReportWriter("timeline_stats", journals.timeline_stats, output_dir_journal).write()
    ReportWriter("dangling_journals_past", journals.dangling_journals_past, output_dir_journal).write()
    ReportWriter("dangling_journals_future", journals.dangling_journals_future, output_dir_journal).write()
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
    ReportWriter("graph_masked_blocks", graph.masked_blocks, output_dir_meta).write()
    # Summary
    for name, data in graph.summary_file_subsets.items():
        ReportWriter(name, data, output_dir_summary).write()
    for name, data in graph.summary_data_subsets.items():
        ReportWriter(name, data, "summary_content_data").write()
    # Namespace
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
    for name, data in namespace_data.items():
        ReportWriter(name, data, output_dir_namespace).write()
    # Move files and assets
    ReportWriter("moved_files", logseq_assets_handler.moved_files, output_dir_assets).write()
    ReportWriter("assets_backlinked", graph.assets_backlinked, output_dir_assets).write()
    ReportWriter("assets_not_backlinked", graph.assets_not_backlinked, output_dir_assets).write()
    if ANALYZER.args.write_graph:
        ReportWriter("___meta___graph_content", graph.content_bullets, output_dir_meta).write()
    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        "___meta___unique_linked_refs_ns": graph.unique_linked_references_ns,
        "___meta___unique_linked_refs": graph.unique_linked_references,
        "___meta___graph_content": graph.content_bullets,
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
    # Update the cache with the new data
    CACHE.update(shelve_output_data)
    CACHE.close()
    # Write user config to file
    ANALYZER_CONFIG.write_to_file()
    gui_instance.update_progress("progress", 100)
