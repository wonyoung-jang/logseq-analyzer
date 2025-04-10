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

    # Get GUI instance if available
    gui_instance = kwargs.get(Phase.GUI_INSTANCE.value, GUIInstanceDummy())
    ###################################################################
    # Phase 01: Setup
    ###################################################################
    gui_instance.update_progress(Phase.PROGRESS.value, 10)
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
    gui_instance.update_progress(Phase.PROGRESS.value, 20)
    graph = LogseqGraph(CACHE)
    gui_instance.update_progress(Phase.PROGRESS.value, 30)
    graph_ns = LogseqNamespaces(graph)
    gui_instance.update_progress(Phase.PROGRESS.value, 40)
    journals = LogseqJournals(graph)
    gui_instance.update_progress(Phase.PROGRESS.value, 60)
    logseq_assets_handler = LogseqFileMover(ANALYZER, ANALYZER_CONFIG, GRAPH_CONFIG, graph)
    gui_instance.update_progress(Phase.PROGRESS.value, 80)
    #####################################################################
    # Phase 05: Outputs
    #####################################################################
    # Output writing
    output_dir_meta = ANALYZER_CONFIG.config["OUTPUT_DIRS"]["META"]
    output_dir_summary = ANALYZER_CONFIG.config["OUTPUT_DIRS"]["SUMMARY"]
    output_dir_namespace = ANALYZER_CONFIG.config["OUTPUT_DIRS"]["NAMESPACE"]
    output_dir_assets = ANALYZER_CONFIG.config["OUTPUT_DIRS"]["ASSETS"]
    output_dir_journal = ANALYZER_CONFIG.config["OUTPUT_DIRS"]["LOGSEQ_JOURNALS"]
    # Journals
    journals_report = {
        Output.DANGLING_JOURNALS.value: journals.dangling_journals,
        Output.PROCESSED_KEYS.value: journals.processed_keys,
        Output.COMPLETE_TIMELINE.value: journals.complete_timeline,
        Output.MISSING_KEYS.value: journals.missing_keys,
        Output.TIMELINE_STATS.value: journals.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: journals.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: journals.dangling_journals_future,
    }
    for name, data in journals_report.items():
        ReportWriter(name, data, output_dir_journal).write()
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
        ReportWriter(name, data, output_dir_meta).write()
    # Summary
    for name, data in graph.summary_file_subsets.items():
        ReportWriter(name, data, output_dir_summary).write()
    for name, data in graph.summary_data_subsets.items():
        ReportWriter(name, data, "summary_content_data").write()
    # Namespace
    namespace_reports = {
        Output.NAMESPACE_DATA.value: graph_ns.namespace_data,
        Output.NAMESPACE_PARTS.value: graph_ns.namespace_parts,
        Output.UNIQUE_NAMESPACE_PARTS.value: graph_ns.unique_namespace_parts,
        Output.NAMESPACE_DETAILS.value: graph_ns.namespace_details,
        Output.UNIQUE_NAMESPACES_PER_LEVEL.value: graph_ns.unique_namespaces_per_level,
        Output.NAMESPACE_QUERIES.value: graph_ns.namespace_queries,
        Output.NAMESPACE_HIERARCHY.value: graph_ns.tree,
        Output.CONFLICTS_NON_NAMESPACE.value: graph_ns.conflicts_non_namespace,
        Output.CONFLICTS_DANGLING.value: graph_ns.conflicts_dangling,
        Output.CONFLICTS_PARENT_DEPTH.value: graph_ns.conflicts_parent_depth,
        Output.CONFLICTS_PARENT_UNIQUE.value: graph_ns.conflicts_parent_unique,
    }
    for name, data in namespace_reports.items():
        ReportWriter(name, data, output_dir_namespace).write()
    # Move files and assets
    moved_files_reports = {
        Output.MOVED_FILES.value: logseq_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    for name, data in moved_files_reports.items():
        ReportWriter(name, data, output_dir_assets).write()
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
        Output.MOVED_FILES.value: logseq_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    # Update the cache with the new data
    CACHE.update(shelve_output_data)
    CACHE.close()
    # Write user config to file
    ANALYZER_CONFIG.write_to_file()
    gui_instance.update_progress(Phase.PROGRESS.value, 100)
