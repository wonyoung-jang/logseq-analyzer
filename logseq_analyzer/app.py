"""
This module contains the main application logic for the Logseq analyzer.
"""

import logging
from pathlib import Path
from typing import Any

from .analysis.assets import LogseqAssets, LogseqAssetsHls
from .analysis.graph import LogseqGraph
from .analysis.index import FileIndex
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .analysis.summary_content import LogseqContentSummarizer
from .analysis.summary_files import LogseqFileSummarizer
from .config.analyzer_config import LogseqAnalyzerConfig
from .config.arguments import Args
from .config.datetime_tokens import LogseqDateTimeTokens, LogseqJournalFormats
from .config.graph_config import LogseqGraphConfig
from .io.cache import Cache
from .io.file_mover import handle_move_directory, handle_move_assets
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
from .logseq_file.file import LogseqFile
from .utils.enums import Moved, Output, OutputDir
from .utils.patterns import ContentPatterns


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    __slots__ = ("progress",)

    def __init__(self) -> None:
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, percentage) -> None:
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %d%%", percentage)


def setup_logseq_arguments(**kwargs) -> Args:
    """Setup Logseq arguments from keyword arguments."""
    a = Args()
    a.setup_args(**kwargs)
    return a


def init_logseq_paths() -> LogFile:
    """Setup Logseq paths for the analyzer."""
    OutputDirectory().initialize_dir()
    lf = LogFile()
    lf.initialize_file()
    return lf


def setup_logging(log_file: Path) -> None:
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


def setup_logseq_analyzer_config(a: Args) -> LogseqAnalyzerConfig:
    """Setup Logseq analyzer configuration based on arguments."""
    lac = LogseqAnalyzerConfig()
    lac.set_value("ANALYZER", "GRAPH_DIR", a.graph_folder)
    lac.set_value("ANALYZER", "REPORT_FORMAT", a.report_format)
    if a.global_config:
        lac.set_value("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", a.global_config)
    logging.debug("run_app: setup_logseq_analyzer_config")
    return lac


def setup_logseq_paths() -> None:
    """Setup Logseq paths for the analyzer."""
    GraphDirectory().validate()
    LogseqDirectory().validate()
    DeleteDirectory().get_or_create_dir()
    DeleteBakDirectory().get_or_create_dir()
    DeleteRecycleDirectory().get_or_create_dir()
    DeleteAssetsDirectory().get_or_create_dir()
    BakDirectory().get_or_create_dir()
    RecycleDirectory().get_or_create_dir()
    logging.debug("run_app: setup_logseq_paths")


def setup_logseq_graph_config(a: Args) -> LogseqGraphConfig:
    """Setup Logseq graph configuration based on arguments."""
    lgc = LogseqGraphConfig()
    cf = ConfigFile()
    cf.validate()
    lgc.initialize_user_config_edn(cf.path)
    if a.global_config:
        gcf = GlobalConfigFile()
        gcf.validate()
        lgc.initialize_global_config_edn(gcf.path)
    lgc.merge()
    logging.debug("run_app: setup_logseq_graph_config")
    return lgc


def setup_target_dirs(lac: LogseqAnalyzerConfig, graph_config: dict[str, str]) -> None:
    """Setup the target directories for the Logseq analyzer by configuring and validating the necessary paths."""
    lac.set_logseq_config_edn_data(graph_config)
    AssetsDirectory().get_or_create_dir()
    DrawsDirectory().get_or_create_dir()
    JournalsDirectory().get_or_create_dir()
    PagesDirectory().get_or_create_dir()
    WhiteboardsDirectory().get_or_create_dir()
    lac.set_logseq_target_dirs()
    logging.debug("run_app: setup_target_dirs")


def setup_datetime_tokens(token_map: dict[str, str], graph_config: dict[str, str]) -> LogseqJournalFormats:
    """Setup datetime tokens."""
    ljf = LogseqJournalFormats()
    ldtt = LogseqDateTimeTokens()
    ldtt.get_datetime_token_map(token_map)
    ldtt.set_datetime_token_pattern()
    ldtt.set_journal_py_formatting(graph_config, ljf)
    del ldtt
    logging.debug("run_app: setup_datetime_tokens")
    return ljf


def setup_cache(a: Args) -> tuple[Cache, FileIndex]:
    """Setup cache for the Logseq Analyzer."""
    c = Cache()
    if a.graph_cache:
        c.clear()
    else:
        c.clear_deleted_files()
    index = FileIndex()
    logging.debug("run_app: setup_cache")
    return c, index


def setup_logseq_graph(index: FileIndex, cache: Cache) -> LogseqGraph:
    """Setup the Logseq graph."""
    lg = LogseqGraph()
    lg.process_graph_files(index, cache)
    lg.post_processing_content(index)
    lg.process_summary_data(index)
    logging.debug("run_app: setup_logseq_graph")
    return lg


def setup_logseq_file_summarizer(index: FileIndex) -> LogseqFileSummarizer:
    """Setup the Logseq file summarizer."""
    lfs = LogseqFileSummarizer()
    lfs.generate_summary(index)
    logging.debug("run_app: setup_logseq_file_summarizer")
    return lfs


def setup_logseq_content_summarizer(index: FileIndex) -> LogseqContentSummarizer:
    """Setup the Logseq content summarizer."""
    lcs = LogseqContentSummarizer()
    lcs.generate_summary(index)
    logging.debug("run_app: setup_logseq_content_summarizer")
    return lcs


def setup_logseq_namespaces(graph: LogseqGraph, index: FileIndex) -> LogseqNamespaces:
    """Setup LogseqNamespaces."""
    ln = LogseqNamespaces()
    ln.init_ns_parts(index)
    ln.analyze_ns_queries(index, ContentPatterns.page_reference)
    ln.detect_non_ns_conflicts(index, graph.dangling_links)
    ln.detect_parent_depth_conflicts()
    logging.debug("run_app: setup_logseq_namespaces")
    return ln


def setup_logseq_journals(graph: LogseqGraph, index: FileIndex, ljf: LogseqJournalFormats) -> LogseqJournals:
    """Setup LogseqJournals."""
    lj = LogseqJournals()
    lj.process_journals_timelines(index, graph, ljf)
    logging.debug("run_app: setup_logseq_journals")
    return lj


def setup_logseq_hls_assets(index: FileIndex) -> LogseqAssetsHls:
    """Setup LogseqAssetsHls for HLS assets."""
    lah = LogseqAssetsHls()
    lah.get_asset_files(index)
    lah.convert_names_to_data(index, ContentPatterns.property_value)
    lah.check_backlinks()
    logging.debug("run_app: setup_logseq_hls_assets")
    return lah


def setup_logseq_assets(index: FileIndex) -> LogseqAssets:
    """Setup LogseqAssets for handling assets."""
    lsa = LogseqAssets()
    lsa.handle_assets(index)
    logging.debug("run_app: setup_logseq_assets")
    return lsa


def setup_logseq_file_mover(args: Args) -> dict[str, Any]:
    """Setup LogseqFileMover for moving files and directories."""
    dbd = DeleteBakDirectory()
    bd = BakDirectory()
    drd = DeleteRecycleDirectory()
    rd = RecycleDirectory()
    dad = DeleteAssetsDirectory()
    lsa = LogseqAssets()
    not_backlinked = lsa.not_backlinked
    moved_files = {}
    moved_files[Moved.ASSETS.value] = handle_move_assets(args.move_unlinked_assets, dad.path, not_backlinked)
    moved_files[Moved.BAK.value] = handle_move_directory(args.move_bak, dbd.path, bd.path)
    moved_files[Moved.RECYCLE.value] = handle_move_directory(args.move_recycle, drd.path, rd.path)
    logging.debug("run_app: setup_logseq_file_mover")
    return moved_files


def get_meta_reports(lg: LogseqGraph, lgc: LogseqGraphConfig, a: Args) -> dict[str, Any]:
    """Get metadata reports from the graph and configuration."""
    index = FileIndex()
    meta_reports = {
        Output.ALL_LINKED_REFERENCES.value: lg.all_linked_references,
        Output.ALL_DANGLING_LINKS.value: lg.all_dangling_links,
        Output.CONFIG_MERGED.value: lgc.config_merged,
        Output.CONFIG_USER.value: lgc._config_user,
        Output.CONFIG_GLOBAL.value: lgc._config_global,
        Output.DANGLING_LINKS.value: lg.dangling_links,
        Output.UNIQUE_LINKED_REFERENCES_NS.value: lg.unique_linked_references_ns,
        Output.UNIQUE_LINKED_REFERENCES.value: lg.unique_linked_references,
        Output.FILES.value: index.files,
        Output.HASH_TO_FILE.value: index.hash_to_file,
        Output.NAME_TO_FILES.value: index.name_to_files,
        Output.PATH_TO_FILE.value: index.path_to_file,
        Output.GRAPH_DATA.value: get_graph_data(index),
    }
    if a.write_graph:
        meta_reports[Output.GRAPH_CONTENT.value] = get_graph_content(index)
    logging.debug("run_app: get_meta_reports")
    return meta_reports


def get_graph_data(index: FileIndex) -> dict[LogseqFile, dict[str, Any]]:
    """Get metadata file data from the graph."""
    graph_data = {}
    for file in index:
        data = {k: v for k, v in file.__dict__.items() if k not in ("content", "content_bullets", "primary_bullet")}
        graph_data[file] = data
    logging.debug("run_app: get_graph_data")
    return graph_data


def get_graph_content(index: FileIndex) -> dict[LogseqFile, list[str]]:
    """Get graph content."""
    logging.debug("run_app: get_graph_content")
    return {file: file.bullets.all_bullets for file in index}


def get_journal_reports(lj: LogseqJournals) -> dict[str, Any]:
    """Get journal reports from the graph journals."""
    logging.debug("run_app: get_journal_reports")
    return {
        Output.DANGLING_JOURNALS.value: lj.dangling_journals,
        Output.PROCESSED_KEYS.value: lj.processed_keys,
        Output.COMPLETE_TIMELINE.value: lj.complete_timeline,
        Output.MISSING_KEYS.value: lj.missing_keys,
        Output.TIMELINE_STATS.value: lj.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: lj.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: lj.dangling_journals_future,
    }


def get_namespace_reports(ln: LogseqNamespaces) -> dict[str, Any]:
    """Get namespace reports from the graph namespaces."""
    logging.debug("run_app: get_namespace_reports")
    return {
        Output.NAMESPACE_DATA.value: ln.namespace_data,
        Output.NAMESPACE_PARTS.value: ln.namespace_parts,
        Output.UNIQUE_NAMESPACE_PARTS.value: ln.unique_namespace_parts,
        Output.NAMESPACE_DETAILS.value: ln.namespace_details,
        Output.UNIQUE_NAMESPACES_PER_LEVEL.value: ln.unique_namespaces_per_level,
        Output.NAMESPACE_QUERIES.value: ln.namespace_queries,
        Output.NAMESPACE_HIERARCHY.value: ln.tree,
        Output.CONFLICTS_NON_NAMESPACE.value: ln.conflicts_non_namespace,
        Output.CONFLICTS_DANGLING.value: ln.conflicts_dangling,
        Output.CONFLICTS_PARENT_DEPTH.value: ln.conflicts_parent_depth,
        Output.CONFLICTS_PARENT_UNIQUE.value: ln.conflicts_parent_unique,
    }


def get_moved_files_reports(moved_files: dict[str, Any], la: LogseqAssets, lah: LogseqAssetsHls) -> dict[str, Any]:
    """Get reports for moved files and assets."""
    logging.debug("run_app: get_moved_files_reports")
    return {
        Output.MOVED_FILES.value: moved_files,
        Output.ASSETS_BACKLINKED.value: la.backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: la.not_backlinked,
        Output.HLS_ASSET_MAPPING.value: lah.asset_mapping,
        Output.HLS_ASSET_NAMES.value: lah.asset_names,
        Output.HLS_FORMATTED_BULLETS.value: lah.formatted_bullets,
        Output.HLS_NOT_BACKLINKED.value: lah.not_backlinked,
        Output.HLS_BACKLINKED.value: lah.backlinked,
    }


def get_output_subdirs() -> list[str]:
    """
    Combine all reports into a single list.

    Returns:
        list[str]: A list of output subdirectories.
    """
    logging.debug("run_app: get_output_subdirs")
    return [
        OutputDir.JOURNALS.value,
        OutputDir.META.value,
        OutputDir.MOVED_FILES.value,
        OutputDir.NAMESPACES.value,
        OutputDir.SUMMARY_CONTENT.value,
        OutputDir.SUMMARY_FILES.value,
    ]


def update_cache(cache: Cache, index: FileIndex) -> None:
    """Update the cache with the current index."""
    cache.cache["index"] = index
    logging.debug("run_app: update_cache")


def write_reports(
    output_subdirs: list[str], data_reports: list[Any], report_format: str, output_dir_path: Path
) -> None:
    """Write reports to the specified output directories."""
    ReportWriter.ext = report_format
    ReportWriter.output_dir = output_dir_path
    for subdir, reports in zip(output_subdirs, data_reports):
        if subdir in (Output.MOD_TRACKER.value):
            continue
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logging.debug("run_app: write_reports")


def run_app(**kwargs) -> None:
    """Main function to run the Logseq analyzer."""
    progress = kwargs.get("progress_callback", GUIInstanceDummy())
    if isinstance(progress, GUIInstanceDummy):
        progress = progress.update_progress
    progress(5)
    args = setup_logseq_arguments(**kwargs)
    progress(10)
    log_file = init_logseq_paths()
    progress(15)
    setup_logging(log_file.path)
    progress(20)
    analyzer_config = setup_logseq_analyzer_config(args)
    progress(25)
    setup_logseq_paths()
    progress(30)
    graph_config = setup_logseq_graph_config(args)
    progress(35)
    setup_target_dirs(analyzer_config, graph_config.config_merged)
    progress(40)
    token_map = analyzer_config.get_section("DATETIME_TOKEN_MAP")
    journal_formats = setup_datetime_tokens(token_map, graph_config.config_merged)
    progress(45)
    cache, index = setup_cache(args)
    progress(50)
    # Main analysis
    graph = setup_logseq_graph(index, cache)
    progress(55)
    summary_files = setup_logseq_file_summarizer(index)
    progress(60)
    summary_content = setup_logseq_content_summarizer(index)
    progress(65)
    graph_namespaces = setup_logseq_namespaces(graph, index)
    progress(70)
    graph_journals = setup_logseq_journals(graph, index, journal_formats)
    progress(75)
    # Assets
    hls_assets = setup_logseq_hls_assets(index)
    progress(80)
    ls_assets = setup_logseq_assets(index)
    progress(85)
    # Move files
    moved_files = setup_logseq_file_mover(args)
    progress(90)
    # Output writing
    meta_reports = get_meta_reports(graph, graph_config, args)
    journal_reports = get_journal_reports(graph_journals)
    namespace_reports = get_namespace_reports(graph_namespaces)
    moved_files_reports = get_moved_files_reports(moved_files, ls_assets, hls_assets)
    output_subdirectories = get_output_subdirs()
    data_reports = [
        journal_reports,
        meta_reports,
        moved_files_reports,
        namespace_reports,
        summary_content.subsets,
        summary_files.subsets,
    ]
    progress(95)
    update_cache(cache, index)
    progress(97)
    report_format = analyzer_config.config["ANALYZER"]["REPORT_FORMAT"]
    output_dir_path = OutputDirectory().path
    write_reports(output_subdirectories, data_reports, report_format, output_dir_path)
    progress(98)
    analyzer_config.write_to_file()
    progress(99)
    cache.close()
    progress(100)
