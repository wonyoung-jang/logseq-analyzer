"""
This module contains the main application logic for the Logseq analyzer.
"""

from pathlib import Path
from typing import List
import logging

from .analysis.index import FileIndex
from .analysis.assets import LogseqAssets, LogseqAssetsHls
from .analysis.graph import LogseqGraph
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .analysis.summary_content import LogseqContentSummarizer
from .analysis.summary_files import LogseqFileSummarizer
from .config.analyzer_config import LogseqAnalyzerConfig
from .config.arguments import Args
from .config.datetime_tokens import LogseqDateTimeTokens
from .config.graph_config import LogseqGraphConfig
from .io.cache import Cache
from .io.file_mover import LogseqFileMover
from .io.filesystem import (
    AssetsDirectory,
    BakDirectory,
    ConfigFile,
    DeleteAssetsDirectory,
    DeleteBakDirectory,
    DeleteDirectory,
    DeleteRecycleDirectory,
    DrawsDirectory,
    GlobalConfigFile,
    GraphDirectory,
    JournalsDirectory,
    LogFile,
    LogseqDirectory,
    OutputDirectory,
    PagesDirectory,
    RecycleDirectory,
    WhiteboardsDirectory,
)
from .io.report_writer import ReportWriter
from .utils.enums import Phase, Output, OutputDir, Moved


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    def __init__(self):
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, percentage):
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %d%%", percentage)


def setup_logseq_arguments(**kwargs) -> Args:
    """Setup Logseq arguments from keyword arguments."""
    args = Args()
    args.setup_args(**kwargs)
    return args


def init_logseq_paths() -> LogFile:
    """Setup Logseq paths for the analyzer."""
    output_dir = OutputDirectory()
    output_dir.initialize_dir()
    log_file = LogFile()
    log_file.initialize_file()
    return log_file


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


def setup_logseq_analyzer_config(args: Args) -> LogseqAnalyzerConfig:
    """Setup Logseq analyzer configuration based on arguments."""
    config = LogseqAnalyzerConfig()
    config.set("ANALYZER", "GRAPH_DIR", args.graph_folder)
    config.set("ANALYZER", "REPORT_FORMAT", args.report_format)
    if args.global_config:
        config.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", args.global_config)
    logging.debug("run_app: setup_logseq_analyzer_config")
    return config


def setup_logseq_paths(args: Args):
    """Setup Logseq paths for the analyzer."""
    graph_dir = GraphDirectory()
    logseq_dir = LogseqDirectory()
    config_file = ConfigFile()
    graph_dir.validate()
    logseq_dir.validate()
    config_file.validate()

    delete_dir = DeleteDirectory()
    delete_bak_dir = DeleteBakDirectory()
    delete_recycle_dir = DeleteRecycleDirectory()
    delete_assets_dir = DeleteAssetsDirectory()
    delete_dir.get_or_create_dir()
    delete_bak_dir.get_or_create_dir()
    delete_recycle_dir.get_or_create_dir()
    delete_assets_dir.get_or_create_dir()

    bak_dir = BakDirectory()
    recycle_dir = RecycleDirectory()
    bak_dir.get_or_create_dir()
    recycle_dir.get_or_create_dir()

    if args.global_config:
        global_config_file = GlobalConfigFile()
        global_config_file.validate()
    logging.debug("run_app: setup_logseq_paths")


def setup_logseq_graph_config() -> LogseqGraphConfig:
    """Setup Logseq graph configuration based on arguments."""
    graph_config = LogseqGraphConfig()
    graph_config.initialize_user_config_edn()
    graph_config.initialize_global_config_edn()
    graph_config.merge()
    logging.debug("run_app: setup_logseq_graph_config")
    return graph_config


def setup_target_dirs(analyzer_config: LogseqAnalyzerConfig, graph_config: LogseqGraphConfig):
    """Setup the target directories for the Logseq analyzer by configuring and validating the necessary paths."""
    analyzer_config.set_logseq_config_edn_data(graph_config.ls_config)
    asset_dir = AssetsDirectory()
    draws_dir = DrawsDirectory()
    journals_dir = JournalsDirectory()
    pages_dir = PagesDirectory()
    whiteboards_dir = WhiteboardsDirectory()
    asset_dir.get_or_create_dir()
    draws_dir.get_or_create_dir()
    journals_dir.get_or_create_dir()
    pages_dir.get_or_create_dir()
    whiteboards_dir.get_or_create_dir()
    analyzer_config.set_logseq_target_dirs()
    logging.debug("run_app: setup_target_dirs")


def setup_datetime_tokens():
    """Setup datetime tokens."""
    dt_tokens = LogseqDateTimeTokens()
    dt_tokens.get_datetime_token_map()
    dt_tokens.set_datetime_token_pattern()
    dt_tokens.set_journal_py_formatting()
    logging.debug("run_app: setup_datetime_tokens")


def setup_cache(args: Args) -> Cache:
    """Setup cache for the Logseq Analyzer."""
    cache = Cache()
    if args.graph_cache:
        cache.clear()
    else:
        cache.clear_deleted_files()
    logging.debug("run_app: setup_cache")
    return cache


def setup_logseq_graph() -> LogseqGraph:
    """Setup the Logseq graph."""
    graph = LogseqGraph()
    graph.process_graph_files()
    graph.post_processing_content()
    graph.process_summary_data()
    logging.debug("run_app: setup_logseq_graph")
    return graph


def setup_logseq_file_summarizer() -> LogseqFileSummarizer:
    """Setup the Logseq file summarizer."""
    summary_files = LogseqFileSummarizer()
    summary_files.generate_summary()
    logging.debug("run_app: setup_logseq_file_summarizer")
    return summary_files


def setup_logseq_content_summarizer() -> LogseqContentSummarizer:
    """Setup the Logseq content summarizer."""
    summary_content = LogseqContentSummarizer()
    summary_content.generate_summary()
    logging.debug("run_app: setup_logseq_content_summarizer")
    return summary_content


def setup_logseq_namespaces() -> LogseqNamespaces:
    """Setup LogseqNamespaces."""
    graph_namespaces = LogseqNamespaces()
    graph_namespaces.init_ns_parts()
    graph_namespaces.analyze_ns_queries()
    graph_namespaces.detect_non_ns_conflicts()
    graph_namespaces.detect_parent_depth_conflicts()
    logging.debug("run_app: setup_logseq_namespaces")
    return graph_namespaces


def setup_logseq_journals() -> LogseqJournals:
    """Setup LogseqJournals."""
    graph_journals = LogseqJournals()
    graph_journals.process_journals_timelines()
    logging.debug("run_app: setup_logseq_journals")
    return graph_journals


def setup_logseq_hls_assets():
    """Setup LogseqAssetsHls for HLS assets."""
    ls_hls = LogseqAssetsHls()
    ls_hls.get_asset_files()
    ls_hls.convert_names_to_data()
    ls_hls.check_backlinks()
    logging.debug("run_app: setup_logseq_hls_assets")
    return ls_hls


def setup_logseq_assets() -> LogseqAssets:
    """Setup LogseqAssets for handling assets."""
    ls_assets = LogseqAssets()
    ls_assets.handle_assets()
    logging.debug("run_app: setup_logseq_assets")
    return ls_assets


def setup_logseq_file_mover(args: Args) -> LogseqFileMover:
    """Setup LogseqFileMover for moving files and directories."""
    ls_file_mover = LogseqFileMover()
    ma = ls_file_mover.handle_move_files()
    mb = ls_file_mover.handle_move_directory(
        args.move_bak,
        DeleteBakDirectory().path,
        BakDirectory().path,
    )
    mr = ls_file_mover.handle_move_directory(
        args.move_recycle,
        DeleteRecycleDirectory().path,
        RecycleDirectory().path,
    )
    ls_file_mover.moved_files[Moved.ASSETS.value] = ma
    ls_file_mover.moved_files[Moved.RECYCLE.value] = mr
    ls_file_mover.moved_files[Moved.BAK.value] = mb
    logging.debug("run_app: setup_logseq_file_mover")
    return ls_file_mover


def get_meta_reports(graph: LogseqGraph, graph_config: LogseqGraphConfig, args: Args) -> dict:
    """Get metadata reports from the graph and configuration."""
    index = FileIndex()
    meta_reports = {
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.CONFIG_DATA.value: graph_config.ls_config,
        "config_user": graph_config.user_config_data,
        "config_global": graph_config.global_config_data,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.UNIQUE_LINKED_REFERENCES_NS.value: graph.unique_linked_references_ns,
        Output.UNIQUE_LINKED_REFERENCES.value: graph.unique_linked_references,
        Output.FILES.value: index.files,
        Output.HASH_TO_FILE.value: index.hash_to_file,
        Output.NAME_TO_FILES.value: index.name_to_files,
        Output.PATH_TO_FILE.value: index.path_to_file,
        Output.GRAPH_DATA.value: get_graph_data(),
    }
    if args.write_graph:
        meta_reports[Output.GRAPH_CONTENT.value] = get_graph_content()
    logging.debug("run_app: get_meta_reports")
    return meta_reports


def get_graph_data() -> dict:
    """Get metadata file data from the graph."""
    index = FileIndex()
    files = index.files
    graph_data = {}
    for file in files:
        data = {k: v for k, v in file.__dict__.items() if k not in ["content", "content_bullets", "primary_bullet"]}
        graph_data[file] = data
    return graph_data


def get_graph_content() -> dict:
    """Get graph content."""
    index = FileIndex()
    files = index.files
    graph_content = {}
    for file in files:
        graph_content[file] = file.bullets.all_bullets
    return graph_content


def get_journal_reports(graph_journals: LogseqJournals) -> dict:
    """Get journal reports from the graph journals."""
    logging.debug("run_app: get_journal_reports")
    return {
        Output.DANGLING_JOURNALS.value: graph_journals.dangling_journals,
        Output.PROCESSED_KEYS.value: graph_journals.processed_keys,
        Output.COMPLETE_TIMELINE.value: graph_journals.complete_timeline,
        Output.MISSING_KEYS.value: graph_journals.missing_keys,
        Output.TIMELINE_STATS.value: graph_journals.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: graph_journals.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: graph_journals.dangling_journals_future,
    }


def get_namespace_reports(graph_namespaces: LogseqNamespaces) -> dict:
    """Get namespace reports from the graph namespaces."""
    logging.debug("run_app: get_namespace_reports")
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


def get_moved_files_reports(
    ls_file_mover: LogseqFileMover, ls_assets: LogseqAssets, hls_assets: LogseqAssetsHls
) -> dict:
    """Get reports for moved files and assets."""
    logging.debug("run_app: get_moved_files_reports")
    return {
        Output.MOVED_FILES.value: ls_file_mover.moved_files,
        Output.ASSETS_BACKLINKED.value: ls_assets.backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: ls_assets.not_backlinked,
        Output.HLS_ASSET_MAPPING.value: hls_assets.asset_mapping,
        Output.HLS_ASSET_NAMES.value: hls_assets.asset_names,
        Output.HLS_FORMATTED_BULLETS.value: hls_assets.formatted_bullets,
        Output.HLS_NOT_BACKLINKED.value: hls_assets.not_backlinked,
        Output.HLS_BACKLINKED.value: hls_assets.backlinked,
    }


def get_main_objects() -> dict:
    """Get main objects for the Logseq analyzer."""
    index = FileIndex()
    graph = LogseqGraph()
    graph_journals = LogseqJournals()
    graph_namespaces = LogseqNamespaces()
    summary_files = LogseqFileSummarizer()
    summary_content = LogseqContentSummarizer()
    return {
        "objects": {
            "all_objects": {
                "index": index,
                "graph": graph,
                "graph_journals": graph_journals,
                "graph_namespaces": graph_namespaces,
                "summary_files": summary_files,
                "summary_content": summary_content,
            }
        }
    }


def get_all_reports() -> List:
    """Combine all reports into a single list."""
    output_subdirectories = [
        OutputDir.JOURNALS,
        OutputDir.META,
        OutputDir.MOVED_FILES,
        OutputDir.NAMESPACES,
        OutputDir.SUMMARY_CONTENT,
        OutputDir.SUMMARY_FILES,
    ]
    logging.debug("run_app: get_all_reports")
    return output_subdirectories


def update_cache(cache: Cache, output_subdirectories: List, data_reports: List):
    """Update the cache with the output data."""
    try:
        shelve_output_data = zip(output_subdirectories, data_reports)
        for output_subdir, data_report in shelve_output_data:
            cache.update({output_subdir.value: data_report})

        cache.update(get_main_objects())

    except Exception as e:
        logging.error("Error updating cache: %s", e)
        raise RuntimeError("Failed to update cache") from e
    logging.debug("run_app: update_cache")


def write_reports(cache: Cache):
    """Write reports to the specified output directories."""
    for output_dir, reports in cache.cache.items():
        if output_dir in (Output.MOD_TRACKER.value):
            continue

        for name, report in reports.items():
            ReportWriter(name, report, output_dir).write()
    logging.debug("run_app: write_reports")


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""
    gui = kwargs.get(Phase.GUI_INSTANCE.value, GUIInstanceDummy())
    progress = gui.update_progress
    progress(5)
    args = setup_logseq_arguments(**kwargs)
    progress(10)
    log_file = init_logseq_paths()
    progress(15)
    setup_logging(log_file.path)
    progress(20)
    analyzer_config = setup_logseq_analyzer_config(args)
    progress(25)
    setup_logseq_paths(args)
    progress(30)
    graph_config = setup_logseq_graph_config()
    progress(35)
    setup_target_dirs(analyzer_config, graph_config)
    progress(40)
    setup_datetime_tokens()
    progress(45)
    cache = setup_cache(args)
    progress(50)
    # Main analysis
    graph = setup_logseq_graph()
    progress(55)
    summary_files = setup_logseq_file_summarizer()
    progress(60)
    summary_content = setup_logseq_content_summarizer()
    progress(65)
    graph_namespaces = setup_logseq_namespaces()
    progress(70)
    graph_journals = setup_logseq_journals()
    progress(75)
    # Assets
    hls_assets = setup_logseq_hls_assets()
    progress(80)
    ls_assets = setup_logseq_assets()
    progress(85)
    # Movee files
    ls_file_mover = setup_logseq_file_mover(args)
    progress(90)
    # Output writing
    meta_reports = get_meta_reports(graph, graph_config, args)
    journal_reports = get_journal_reports(graph_journals)
    namespace_reports = get_namespace_reports(graph_namespaces)
    moved_files_reports = get_moved_files_reports(ls_file_mover, ls_assets, hls_assets)
    output_subdirectories = get_all_reports()
    data_reports = [
        journal_reports,
        meta_reports,
        moved_files_reports,
        namespace_reports,
        summary_content.subsets,
        summary_files.subsets,
    ]
    progress(95)
    update_cache(cache, output_subdirectories, data_reports)
    progress(97)
    write_reports(cache)
    progress(98)
    analyzer_config.write_to_file()
    progress(99)
    cache.close()
    progress(100)
