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
from .utils.enums import Phase, Output, SummaryFiles, OutputDir, Moved


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    def __init__(self):
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, percentage):
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %d%%", percentage)


def setup_logseq_arguments(**kwargs):
    """Setup Logseq arguments from keyword arguments."""
    args = LogseqAnalyzerArguments()
    args.setup_args(**kwargs)
    return args


def init_logseq_paths():
    """Setup Logseq paths for the analyzer."""
    paths = LogseqAnalyzerPathValidator()
    paths.validate_output_dir_and_logging()
    return paths


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


def setup_logseq_analyzer_config(args: LogseqAnalyzerArguments) -> LogseqAnalyzerConfig:
    """Setup Logseq analyzer configuration based on arguments."""
    config = LogseqAnalyzerConfig()
    config.set("ANALYZER", "GRAPH_DIR", args.graph_folder)
    config.set("ANALYZER", "REPORT_FORMAT", args.report_format)
    if args.global_config:
        config.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", args.global_config)
    return config


def setup_logseq_paths(paths, args: LogseqAnalyzerArguments) -> LogseqAnalyzerPathValidator:
    """Setup Logseq paths for the analyzer."""
    paths.validate_graph_logseq_config_paths()
    paths.validate_analyzer_paths()
    paths.validate_graph_paths()
    if args.global_config:
        paths.validate_global_config_path()
    return paths


def setup_logseq_graph_config(args: LogseqAnalyzerArguments, paths: LogseqAnalyzerPathValidator) -> LogseqGraphConfig:
    """Setup Logseq graph configuration based on arguments."""
    graph_config = LogseqGraphConfig()
    if args.global_config:
        graph_config.global_config_file = paths.file_config_global.path
    graph_config.user_config_file = paths.file_config.path
    graph_config.initialize_user_config_edn()
    graph_config.initialize_global_config_edn()
    graph_config.merge()
    return graph_config


def setup_target_dirs(ac: LogseqAnalyzerConfig, gc: LogseqGraphConfig, paths: LogseqAnalyzerPathValidator):
    """Setup the target directories for the Logseq analyzer by configuring and validating the necessary paths."""
    ac.set_logseq_config_edn_data(gc.ls_config)
    paths.validate_target_paths()
    ac.set_logseq_target_dirs()


def setup_datetime_tokens():
    """Setup datetime tokens."""
    LogseqDateTimeTokens().get_datetime_token_map()
    LogseqDateTimeTokens().set_datetime_token_pattern()
    LogseqDateTimeTokens().set_journal_py_formatting()


def setup_cache(graph_cache: bool) -> Cache:
    """Setup cache for the Logseq Analyzer."""
    cache = Cache()
    if graph_cache:
        cache.clear()
    else:
        cache.clear_deleted_files()
    return cache


def setup_logseq_graph():
    """Setup the Logseq graph."""
    graph = LogseqGraph()
    graph.process_graph_files()
    graph.update_graph_files_with_cache()
    graph.post_processing_content()
    graph.process_summary_data()
    return graph


def setup_logseq_file_summarizer():
    """Setup the Logseq file summarizer."""
    summary_files = LogseqFileSummarizer()
    summary_files.generate_summary()
    return summary_files


def setup_logseq_content_summarizer():
    """Setup the Logseq content summarizer."""
    summary_content = LogseqContentSummarizer()
    summary_content.generate_summary()
    return summary_content


def setup_logseq_namespaces():
    """Setup LogseqNamespaces."""
    graph_namespaces = LogseqNamespaces()
    graph_namespaces.init_ns_parts()
    graph_namespaces.analyze_ns_queries()
    graph_namespaces.detect_non_ns_conflicts()
    graph_namespaces.detect_parent_depth_conflicts()
    return graph_namespaces


def setup_logseq_journals():
    """Setup LogseqJournals."""
    graph_journals = LogseqJournals()
    graph_journals.process_journals_timelines()
    return graph_journals


def setup_logseq_hls_assets(summary_files):
    """Setup LogseqAssetsHls for HLS assets."""
    names = summary_files.subsets.get(SummaryFiles.IS_HLS.value, [])
    ls_hls = LogseqAssetsHls()
    ls_hls.get_asset_files()
    ls_hls.convert_names_to_data(names)
    ls_hls.check_backlinks()


def setup_logseq_assets(summary_files):
    """Setup LogseqAssets for handling assets."""
    asset_files = summary_files.subsets.get(SummaryFiles.FILETYPE_ASSET.value, [])
    ls_assets = LogseqAssets()
    ls_assets.handle_assets(asset_files)
    return ls_assets


def setup_logseq_file_mover(args, paths):
    """Setup LogseqFileMover for moving files and directories."""
    ls_file_mover = LogseqFileMover()
    ma = ls_file_mover.handle_move_files()
    mb = ls_file_mover.handle_move_directory(
        args.move_bak,
        paths.dir_delete_bak.path,
        paths.dir_bak.path,
    )
    mr = ls_file_mover.handle_move_directory(
        args.move_recycle,
        paths.dir_delete_recycle.path,
        paths.dir_recycle.path,
    )
    ls_file_mover.moved_files[Moved.ASSETS.value] = ma
    ls_file_mover.moved_files[Moved.RECYCLE.value] = mr
    ls_file_mover.moved_files[Moved.BAK.value] = mb
    return ls_file_mover


def get_meta_reports(graph, graph_config, args):
    """Get metadata reports from the graph and configuration."""
    meta_reports = {
        Output.UNIQUE_LINKED_REFERENCES.value: graph.unique_linked_references,
        Output.UNIQUE_LINKED_REFERENCES_NS.value: graph.unique_linked_references_ns,
        Output.GRAPH_DATA.value: graph.data,
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.GRAPH_HASHED_FILES.value: graph.hash_to_file_map,
        Output.GRAPH_NAMES_TO_HASHES.value: graph.name_to_hashes_map,
        Output.CONFIG_DATA.value: graph_config.ls_config,
    }
    if args.write_graph:
        meta_reports[Output.GRAPH_CONTENT.value] = graph.content_bullets
    return meta_reports


def get_journal_reports(graph_journals):
    """Get journal reports from the graph journals."""
    return {
        Output.DANGLING_JOURNALS.value: graph_journals.dangling_journals,
        Output.PROCESSED_KEYS.value: graph_journals.processed_keys,
        Output.COMPLETE_TIMELINE.value: graph_journals.complete_timeline,
        Output.MISSING_KEYS.value: graph_journals.missing_keys,
        Output.TIMELINE_STATS.value: graph_journals.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: graph_journals.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: graph_journals.dangling_journals_future,
    }


def get_namespace_reports(graph_namespaces):
    """Get namespace reports from the graph namespaces."""
    return {
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


def get_moved_files_reports(ls_file_mover, ls_assets):
    """Get reports for moved files and assets."""
    return {
        Output.MOVED_FILES.value: ls_file_mover.moved_files,
        Output.ASSETS_BACKLINKED.value: ls_assets.backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: ls_assets.not_backlinked,
    }


def get_all_reports(
    meta_reports, journal_reports, summary_files, summary_content, namespace_reports, moved_files_reports
):
    """Combine all reports into a single dictionary."""
    return [
        (meta_reports, OutputDir.META),
        (journal_reports, OutputDir.JOURNALS),
        (summary_files.subsets, OutputDir.SUMMARY_FILES),
        (summary_content.subsets, OutputDir.SUMMARY_CONTENT),
        (namespace_reports, OutputDir.NAMESPACES),
        (moved_files_reports, OutputDir.MOVED_FILES),
    ]


def write_reports(reports):
    """Write reports to the specified output directories."""
    for report, output_dir in reports:
        for name, data in report.items():
            ReportWriter(name, data, output_dir.value).write()


def update_cache_and_write_config(
    analyzer_config,
    cache,
    summary_files,
    summary_content,
    meta_reports,
    journal_reports,
    namespace_reports,
    moved_files_reports,
):
    """Update the cache with the output data and write the analyzer configuration to file."""
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


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""
    gui = kwargs.get(Phase.GUI_INSTANCE.value, GUIInstanceDummy())
    progress = gui.update_progress
    progress(5)
    args = setup_logseq_arguments(**kwargs)
    paths = init_logseq_paths()
    setup_logging(paths.file_log.path)
    # --- #
    analyzer_config = setup_logseq_analyzer_config(args)
    setup_logseq_paths(paths, args)
    progress(10)
    graph_config = setup_logseq_graph_config(args, paths)
    setup_target_dirs(analyzer_config, graph_config, paths)
    # --- #
    setup_datetime_tokens()
    progress(20)
    cache = setup_cache(args.graph_cache)
    progress(30)
    # Main analysis
    graph = setup_logseq_graph()
    progress(40)
    summary_files = setup_logseq_file_summarizer()
    progress(50)
    summary_content = setup_logseq_content_summarizer()
    progress(60)
    graph_namespaces = setup_logseq_namespaces()
    progress(70)
    graph_journals = setup_logseq_journals()
    progress(80)
    # Assets
    setup_logseq_hls_assets(summary_files)
    ls_assets = setup_logseq_assets(summary_files)
    progress(85)
    # Movee files
    ls_file_mover = setup_logseq_file_mover(args, paths)
    progress(90)
    # Output writing
    meta_reports = get_meta_reports(graph, graph_config, args)
    journal_reports = get_journal_reports(graph_journals)
    namespace_reports = get_namespace_reports(graph_namespaces)
    moved_files_reports = get_moved_files_reports(ls_file_mover, ls_assets)
    all_outputs = get_all_reports(
        meta_reports, journal_reports, summary_files, summary_content, namespace_reports, moved_files_reports
    )
    write_reports(all_outputs)
    progress(95)
    # Cache writing
    update_cache_and_write_config(
        analyzer_config,
        cache,
        summary_files,
        summary_content,
        meta_reports,
        journal_reports,
        namespace_reports,
        moved_files_reports,
    )
    progress(100)
