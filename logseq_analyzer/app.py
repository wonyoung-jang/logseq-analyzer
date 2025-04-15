"""
This module contains the main application logic for the Logseq analyzer.
"""

from pathlib import Path
import logging

from .analysis.assets import LogseqAssets, LogseqAssetsHls
from .analysis.graph import LogseqGraph
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .analysis.summary_content import LogseqContentSummarizer
from .analysis.summary_files import LogseqFileSummarizer
from .config.analyzer_config import LogseqAnalyzerConfig
from .config.arguments import LogseqAnalyzerArguments
from .config.datetime_tokens import LogseqDateTimeTokens
from .config.graph_config import LogseqGraphConfig
from .io.cache import Cache
from .io.file_mover import LogseqFileMover
from .io.path_validator import LogseqAnalyzerPathValidator
from .io.report_writer import ReportWriter
from .utils.enums import Phase, Output, SummaryFiles


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
    analyzer_config = LogseqAnalyzerConfig()
    graph_config = LogseqGraphConfig()
    paths.validate_cache()
    cache = Cache(paths.file_cache.path)
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
    graph_config.initialize_user_config_edn()
    graph_config.initialize_global_config_edn()
    graph_config.merge()
    analyzer_config.set_logseq_config_edn_data(graph_config.ls_config)
    paths.validate_target_paths()
    # --- #
    analyzer_config.get_logseq_target_dirs()
    datetime_tokens = LogseqDateTimeTokens(analyzer_config)
    datetime_tokens.get_datetime_token_map()
    datetime_tokens.set_datetime_token_pattern()
    datetime_tokens.set_journal_py_formatting()
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
    summary_files = LogseqFileSummarizer()
    summary_files.generate_summary()
    progress(70)
    summary_content = LogseqContentSummarizer()
    summary_content.generate_summary()
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

    summary_subset_hls_files = summary_files.subsets.get(SummaryFiles.IS_HLS.value, [])
    ls_hls_assets = LogseqAssetsHls()
    ls_hls_assets.get_asset_files()
    ls_hls_assets.convert_names_to_data(summary_subset_hls_files)
    ls_hls_assets.check_backlinks()

    summary_subset_assets = summary_files.subsets.get(SummaryFiles.FILETYPE_ASSET.value, [])
    ls_assets = LogseqAssets()
    ls_assets.handle_assets(summary_subset_assets)

    ls_file_mover = LogseqFileMover()
    moved_files = ls_file_mover.moved_files
    moved_files["moved_assets"] = ls_file_mover.handle_move_files()
    moved_files["moved_bak"] = ls_file_mover.handle_move_directory(
        args.move_bak,
        paths.dir_delete_bak.path,
        paths.dir_bak.path,
    )
    moved_files["moved_recycle"] = ls_file_mover.handle_move_directory(
        args.move_recycle,
        paths.dir_delete_recycle.path,
        paths.dir_recycle.path,
    )
    progress(95)
    # Output writing
    meta_reports = {
        Output.META_UNIQUE_LINKED_REFS.value: graph.unique_linked_references,
        Output.META_UNIQUE_LINKED_REFS_NS.value: graph.unique_linked_references_ns,
        Output.GRAPH_DATA.value: graph.data,
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.GRAPH_HASHED_FILES.value: graph.hash_to_file_map,
        Output.GRAPH_NAMES_TO_HASHES.value: graph.name_to_hashes_map,
        Output.GRAPH_MASKED_BLOCKS.value: graph.masked_blocks,
        Output.CONFIG_DATA.value: graph_config.ls_config,
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
        Output.MOVED_FILES.value: ls_file_mover.moved_files,
        Output.ASSETS_BACKLINKED.value: ls_assets.backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: ls_assets.not_backlinked,
    }
    # Writing
    all_outputs = (
        (meta_reports, analyzer_config.config["OUTPUT"]["META"]),
        (journal_reports, analyzer_config.config["OUTPUT"]["JOURNALS"]),
        (summary_files.subsets, analyzer_config.config["OUTPUT"]["SUMMARY_FILE"]),
        (summary_content.subsets, analyzer_config.config["OUTPUT"]["SUMMARY_CONTENT"]),
        (namespace_reports, analyzer_config.config["OUTPUT"]["NAMESPACES"]),
        (moved_files_reports, analyzer_config.config["OUTPUT"]["ASSETS"]),
    )
    for report, output_dir in all_outputs:
        for name, data in report.items():
            ReportWriter(name, data, output_dir).write()

    # Cache writing
    try:
        shelve_output_data = {
            **meta_reports,
            **summary_files.subsets,
            **summary_content.subsets,
            **journal_reports,
            **namespace_reports,
            **moved_files_reports,
        }
        cache.update(shelve_output_data)
        cache.close()
    finally:
        analyzer_config.write_to_file()
    progress(100)
