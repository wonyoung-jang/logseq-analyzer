"""
This module contains the main application logic for the Logseq analyzer.
"""

from enum import Enum

from .logseq_analyzer_config import ANALYZER_CONFIG
from .logseq_analyzer import ANALYZER
from .logseq_graph_config import GRAPH_CONFIG
from .cache import CACHE
from .logseq_graph import LogseqGraph
from .logseq_file_mover import LogseqFileMover
from .logseq_journals import LogseqJournals
from .logseq_namespaces import LogseqNamespaces
from .report_writer import ReportWriter
import logging


class Phase(Enum):
    GUI_INSTANCE = "gui_instance"
    PROGRESS = "progress"


class Output(Enum):
    DANGLING_JOURNALS = "dangling_journals"
    PROCESSED_KEYS = "processed_keys"
    COMPLETE_TIMELINE = "complete_timeline"
    MISSING_KEYS = "missing_keys"
    TIMELINE_STATS = "timeline_stats"
    DANGLING_JOURNALS_PAST = "dangling_journals_past"
    DANGLING_JOURNALS_FUTURE = "dangling_journals_future"
    META_UNIQUE_LINKED_REFS = "___meta___unique_linked_refs"
    META_UNIQUE_LINKED_REFS_NS = "___meta___unique_linked_refs_ns"
    GRAPH_DATA = "___meta___graph_data"
    GRAPH_CONTENT = "___meta___graph_content"
    ALL_REFS = "all_refs"
    DANGLING_LINKS = "dangling_links"
    GRAPH_HASHED_FILES = "graph_hashed_files"
    GRAPH_NAMES_TO_HASHES = "graph_names_to_hashes"
    GRAPH_MASKED_BLOCKS = "graph_masked_blocks"
    NAMESPACE_DATA = "___meta___namespace_data"
    NAMESPACE_PARTS = "___meta___namespace_parts"
    UNIQUE_NAMESPACE_PARTS = "unique_namespace_parts"
    NAMESPACE_DETAILS = "namespace_details"
    UNIQUE_NAMESPACES_PER_LEVEL = "unique_namespaces_per_level"
    NAMESPACE_QUERIES = "namespace_queries"
    NAMESPACE_HIERARCHY = "namespace_hierarchy"
    CONFLICTS_NON_NAMESPACE = "conflicts_non_namespace"
    CONFLICTS_DANGLING = "conflicts_dangling"
    CONFLICTS_PARENT_DEPTH = "conflicts_parent_depth"
    CONFLICTS_PARENT_UNIQUE = "conflicts_parent_unique"
    MOVED_FILES = "moved_files"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"


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
    gui = kwargs.get(Phase.GUI_INSTANCE.value, GUIInstanceDummy())
    gui.update_progress(Phase.PROGRESS.value, 10)
    ANALYZER.get_logseq_analyzer_args(**kwargs)
    ANALYZER.create_output_directory()
    ANALYZER.create_log_file()
    ANALYZER.create_delete_directory()
    GRAPH_CONFIG.initialize_graph()
    GRAPH_CONFIG.initialize_config()
    ANALYZER_CONFIG.get_built_in_properties()
    ANALYZER_CONFIG.get_datetime_token_map()
    ANALYZER_CONFIG.get_datetime_token_pattern()
    ANALYZER_CONFIG.set("ANALYZER", "REPORT_FORMAT", ANALYZER.args.report_format)
    ANALYZER_CONFIG.set("ANALYZER", "GRAPH_DIR", GRAPH_CONFIG.directory)
    ANALYZER_CONFIG.set_logseq_config_edn_data(GRAPH_CONFIG.ls_config)
    ANALYZER_CONFIG.get_logseq_target_dirs()
    ANALYZER_CONFIG.set_journal_py_formatting()
    if ANALYZER.args.graph_cache:
        CACHE.clear()
    else:
        CACHE.clear_deleted_files()
    gui.update_progress(Phase.PROGRESS.value, 20)

    graph = LogseqGraph(CACHE)
    graph.process_graph_files()
    gui.update_progress(Phase.PROGRESS.value, 30)

    graph.update_graph_files_with_cache()
    gui.update_progress(Phase.PROGRESS.value, 40)

    graph.post_processing_content()
    gui.update_progress(Phase.PROGRESS.value, 50)

    graph.process_summary_data()
    gui.update_progress(Phase.PROGRESS.value, 60)

    graph.generate_summary_file_subsets()
    gui.update_progress(Phase.PROGRESS.value, 70)

    graph.generate_summary_data_subsets()
    gui.update_progress(Phase.PROGRESS.value, 80)

    graph_namespaces = LogseqNamespaces(graph)
    graph_namespaces.init_ns_parts()
    graph_namespaces.analyze_ns_queries()
    graph_namespaces.detect_non_ns_conflicts()
    graph_namespaces.detect_parent_depth_conflicts()
    gui.update_progress(Phase.PROGRESS.value, 85)

    graph_journals = LogseqJournals(graph)
    graph_journals.process_journals_timelines()
    gui.update_progress(Phase.PROGRESS.value, 90)

    graph_assets_handler = LogseqFileMover(ANALYZER, ANALYZER_CONFIG, GRAPH_CONFIG, graph)
    gui.update_progress(Phase.PROGRESS.value, 95)

    # Output writing
    # Meta
    meta_reports = {
        Output.META_UNIQUE_LINKED_REFS.value: graph.unique_linked_references,
        Output.META_UNIQUE_LINKED_REFS_NS.value: graph.unique_linked_references_ns,
        Output.GRAPH_DATA.value: graph.data,
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.GRAPH_HASHED_FILES.value: graph.hashed_files,
        Output.GRAPH_NAMES_TO_HASHES.value: graph.names_to_hashes,
        Output.GRAPH_MASKED_BLOCKS.value: graph.masked_blocks,
    }
    if ANALYZER.args.write_graph:
        meta_reports[Output.GRAPH_CONTENT.value] = graph.content_bullets
    for name, data in meta_reports.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["META"]).write()
    # Journals
    journals_report = {
        Output.DANGLING_JOURNALS.value: graph_journals.dangling_journals,
        Output.PROCESSED_KEYS.value: graph_journals.processed_keys,
        Output.COMPLETE_TIMELINE.value: graph_journals.complete_timeline,
        Output.MISSING_KEYS.value: graph_journals.missing_keys,
        Output.TIMELINE_STATS.value: graph_journals.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: graph_journals.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: graph_journals.dangling_journals_future,
    }
    for name, data in journals_report.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["LOGSEQ_JOURNALS"]).write()
    # Summary
    for name, data in graph.summary_file_subsets.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["SUMMARY"]).write()
    for name, data in graph.summary_data_subsets.items():
        ReportWriter(name, data, "summary_content_data").write()
    # Namespace
    namespace_reports = {
        Output.NAMESPACE_DATA.value: graph_namespaces.namespace_data,
        Output.NAMESPACE_PARTS.value: graph_namespaces.namespace_parts,
        Output.UNIQUE_NAMESPACE_PARTS.value: graph_namespaces.unique_namespace_parts,
        Output.NAMESPACE_DETAILS.value: graph_namespaces.namespace_details,
        Output.UNIQUE_NAMESPACES_PER_LEVEL.value: graph_namespaces.unique_namespaces_per_level,
        Output.NAMESPACE_QUERIES.value: graph_namespaces.namespace_queries,
        Output.NAMESPACE_HIERARCHY.value: graph_namespaces.tree,
        Output.CONFLICTS_NON_NAMESPACE.value: graph_namespaces.conflicts_non_namespace,
        Output.CONFLICTS_DANGLING.value: graph_namespaces.conflicts_dangling,
        Output.CONFLICTS_PARENT_DEPTH.value: graph_namespaces.conflicts_parent_depth,
        Output.CONFLICTS_PARENT_UNIQUE.value: graph_namespaces.conflicts_parent_unique,
    }
    for name, data in namespace_reports.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["NAMESPACE"]).write()
    # Move files and assets
    moved_files_reports = {
        Output.MOVED_FILES.value: graph_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    for name, data in moved_files_reports.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["ASSETS"]).write()
    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        Output.META_UNIQUE_LINKED_REFS.value: graph.unique_linked_references,
        Output.META_UNIQUE_LINKED_REFS_NS.value: graph.unique_linked_references_ns,
        Output.GRAPH_DATA.value: graph.data,
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.GRAPH_HASHED_FILES.value: graph.hashed_files,
        Output.GRAPH_NAMES_TO_HASHES.value: graph.names_to_hashes,
        Output.GRAPH_MASKED_BLOCKS.value: graph.masked_blocks,
        # General summary
        **graph.summary_file_subsets,
        **graph.summary_data_subsets,
        # Namespaces summary
        **namespace_reports,
        # Move files and assets
        Output.MOVED_FILES.value: graph_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    try:
        CACHE.update(shelve_output_data)
        CACHE.close()
    finally:
        ANALYZER_CONFIG.write_to_file()
    gui.update_progress(Phase.PROGRESS.value, 100)
