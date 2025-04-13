"""
This module contains the main application logic for the Logseq analyzer.
"""

from pathlib import Path
import logging

from .analysis.graph import LogseqGraph
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .config.analyzer_config import LogseqAnalyzerConfig
from .config.arguments import LogseqAnalyzerArguments
from .config.graph_config import LogseqGraphConfig
from .io.cache import Cache
from .io.file_mover import LogseqFileMover
from .io.path_validator import LogseqAnalyzerPathValidator
from .io.report_writer import ReportWriter
from .utils.enums import Phase, Output
from .utils.patterns import RegexPatterns


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    def __init__(self):
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, phase, percentage):
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %s - %d%%", phase, percentage)


def setup_logging(log_file: Path):
    """Setup logging configuration for the Logseq Analyzer."""
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    logging.info("Logseq Analyzer started.")
    logging.debug("Logging initialized to %s", log_file)


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""
    gui = kwargs.get(Phase.GUI_INSTANCE.value, GUIInstanceDummy())
    progress = gui.update_progress
    progress(5)
    args = LogseqAnalyzerArguments()
    args.setup_args(**kwargs)
    paths = LogseqAnalyzerPathValidator()
    paths.validate_output_dir_and_logging()
    setup_logging(paths.file_log.path)
    # --- #
    patterns = RegexPatterns()
    patterns.compile_re_content()
    patterns.compile_re_content_double_curly_brackets()
    patterns.compile_re_content_advanced_command()
    patterns.compile_re_ext_links()
    patterns.compile_re_emb_links()
    patterns.compile_re_code()
    patterns.compile_re_dblparen()
    analyzer_config = LogseqAnalyzerConfig()
    graph_config = LogseqGraphConfig()
    paths.validate_cache()
    cache = Cache()
    analyzer_config.set("ANALYZER", "GRAPH_DIR", args.graph_folder)
    paths.validate_graph_logseq_config_paths()
    progress(10)
    paths.validate_analyzer_paths()
    analyzer_config.set("ANALYZER", "REPORT_FORMAT", args.report_format)
    paths.validate_graph_paths()
    if args.global_config:
        analyzer_config.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", args.global_config)
        paths.validate_global_config_path()
        graph_config.global_config_file = paths.file_config_global.path
    graph_config.user_config_file = paths.file_config.path
    graph_config.initialize_config_edns()
    analyzer_config.set_logseq_config_edn_data(graph_config.ls_config)
    paths.validate_target_paths()
    analyzer_config.get_logseq_target_dirs()
    analyzer_config.get_built_in_properties()
    analyzer_config.get_datetime_token_map()
    analyzer_config.get_datetime_token_pattern()
    analyzer_config.set_journal_py_formatting()
    if args.graph_cache:
        cache.clear()
    else:
        cache.clear_deleted_files()
    progress(20)
    graph = LogseqGraph()
    graph.process_graph_files()
    progress(30)
    graph.update_graph_files_with_cache()
    progress(40)
    graph.post_processing_content()
    progress(50)
    graph.process_summary_data()
    progress(60)
    graph.generate_summary_file_subsets()
    progress(70)
    graph.generate_summary_data_subsets()
    progress(80)
    graph_namespaces = LogseqNamespaces()
    graph_namespaces.init_ns_parts()
    graph_namespaces.analyze_ns_queries()
    graph_namespaces.detect_non_ns_conflicts()
    graph_namespaces.detect_parent_depth_conflicts()
    progress(85)
    graph_journals = LogseqJournals()
    graph_journals.process_journals_timelines()
    progress(90)
    graph.handle_assets()
    graph_assets_handler = LogseqFileMover()
    moved_files = graph_assets_handler.moved_files
    moved_files["moved_assets"] = graph_assets_handler.handle_move_files()
    moved_files["moved_bak"] = graph_assets_handler.handle_move_directory(
        args.move_bak,
        paths.dir_bak.path,
        analyzer_config.config["CONST"]["BAK_DIR"],
    )
    moved_files["moved_recycle"] = graph_assets_handler.handle_move_directory(
        args.move_recycle,
        paths.dir_recycle.path,
        analyzer_config.config["CONST"]["RECYCLE_DIR"],
    )
    progress(95)
    # Output writing
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
    if args.write_graph:
        meta_reports[Output.GRAPH_CONTENT.value] = graph.content_bullets
    # Journals
    journal_reports = {
        Output.DANGLING_JOURNALS.value: graph_journals.dangling_journals,
        Output.PROCESSED_KEYS.value: graph_journals.processed_keys,
        Output.COMPLETE_TIMELINE.value: graph_journals.complete_timeline,
        Output.MISSING_KEYS.value: graph_journals.missing_keys,
        Output.TIMELINE_STATS.value: graph_journals.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: graph_journals.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: graph_journals.dangling_journals_future,
    }
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
    # Move files and assets
    moved_files_reports = {
        Output.MOVED_FILES.value: graph_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    # Writing
    all_outputs = [
        (meta_reports, analyzer_config.config["OUTPUT"]["META"]),
        (journal_reports, analyzer_config.config["OUTPUT"]["JOURNALS"]),
        (graph.summary_file_subsets, analyzer_config.config["OUTPUT"]["SUMMARY_FILE"]),
        (graph.summary_data_subsets, analyzer_config.config["OUTPUT"]["SUMMARY_CONTENT"]),
        (namespace_reports, analyzer_config.config["OUTPUT"]["NAMESPACES"]),
        (moved_files_reports, analyzer_config.config["OUTPUT"]["ASSETS"]),
    ]
    for report, output_dir in all_outputs:
        for name, data in report.items():
            ReportWriter(name, data, output_dir).write()
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
        cache.update(shelve_output_data)
        cache.close()
    finally:
        analyzer_config.write_to_file()
    progress(100)
