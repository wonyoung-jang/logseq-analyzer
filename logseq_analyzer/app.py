"""
This module contains the main application logic for the Logseq analyzer.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import logseq_analyzer.utils.patterns_content as ContentPatterns
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
    CacheFile,
    ConfigFile,
    ConfigIniFile,
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
    UserConfigIniFile,
    WhiteboardsDirectory,
)
from .io.report_writer import ReportWriter
from .logseq_file.file import LogseqFile
from .logseq_file.name import LogseqFilename
from .utils.enums import Config, Constants, Moved, Output, OutputDir


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    __slots__ = ("progress",)

    def __init__(self) -> None:
        """Initialize dummy GUI instance."""
        self.progress = {}

    def __repr__(self) -> str:
        """Return a string representation of the dummy GUI instance."""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """Return a string representation of the dummy GUI instance."""
        return f"{self.__class__.__name__}"

    def update_progress(self, percentage) -> None:
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %d%%", percentage)


@dataclass
class Configurations:
    """Class to hold configurations for the Logseq analyzer."""

    analyzer: LogseqAnalyzerConfig
    graph: LogseqGraphConfig
    journal_formats: LogseqJournalFormats


def setup_logseq_arguments(**kwargs) -> Args:
    """Setup Logseq arguments from keyword arguments."""
    a = Args()
    a.setup_args(**kwargs)
    return a


def init_logseq_paths() -> LogFile:
    """Setup Logseq paths for the analyzer."""
    output_dir = Constants.OUTPUT_DIR.value
    OutputDirectory(output_dir)

    log_file_path = Constants.LOG_FILE.value
    lf = LogFile(log_file_path)
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
    path = Path.cwd() / Constants.CONFIG_INI_FILE.value
    if not path.exists():
        path = Path.cwd() / "_internal" / Constants.CONFIG_INI_FILE.value
    config_ini_file = ConfigIniFile(path)
    lac = LogseqAnalyzerConfig(config_ini_file.path)
    lac.set_value("ANALYZER", "GRAPH_DIR", a.graph_folder)
    lac.set_value("ANALYZER", "REPORT_FORMAT", a.report_format)
    if a.global_config:
        lac.set_value("ANALYZER", "GLOBAL_CONFIG_FILE", a.global_config)
    logging.debug("run_app: setup_logseq_analyzer_config")
    return lac


def setup_logseq_paths(lac: LogseqAnalyzerConfig) -> None:
    """Setup Logseq paths for the analyzer."""
    graph_dir = lac["ANALYZER"]["GRAPH_DIR"]
    logseq_dir = lac["ANALYZER"]["LOGSEQ_DIR"]
    bak_dir = lac["ANALYZER"]["BAK_DIR"]
    recycle_dir = lac["ANALYZER"]["RECYCLE_DIR"]
    GraphDirectory(graph_dir)
    LogseqDirectory(logseq_dir)
    BakDirectory(bak_dir)
    RecycleDirectory(recycle_dir)

    delete_dir = Constants.TO_DELETE_DIR.value
    delete_bak_dir = Constants.TO_DELETE_BAK_DIR.value
    delete_recycle_dir = Constants.TO_DELETE_RECYCLE_DIR.value
    delete_assets_dir = Constants.TO_DELETE_ASSETS_DIR.value
    DeleteDirectory(delete_dir)
    DeleteBakDirectory(delete_bak_dir)
    DeleteRecycleDirectory(delete_recycle_dir)
    DeleteAssetsDirectory(delete_assets_dir)
    logging.debug("run_app: setup_logseq_paths")


def setup_logseq_graph_config(a: Args, lac: LogseqAnalyzerConfig) -> LogseqGraphConfig:
    """Setup Logseq graph configuration based on arguments."""
    lgc = LogseqGraphConfig()
    config_path = lac["ANALYZER"]["USER_CONFIG_FILE"]
    cf = ConfigFile(config_path)
    lgc.initialize_user_config_edn(cf.path)
    if a.global_config:
        global_config_path = lac["ANALYZER"]["GLOBAL_CONFIG_FILE"]
        gcf = GlobalConfigFile(global_config_path)
        lgc.initialize_global_config_edn(gcf.path)
    lgc.merge()
    logging.debug("run_app: setup_logseq_graph_config")
    return lgc


def setup_target_dirs(lac: LogseqAnalyzerConfig, config: dict[str, str]) -> None:
    """Setup the target directories for the Logseq analyzer by configuring and validating the necessary paths."""
    lac.set_logseq_config_edn_data(config)
    dir_assets = lac["TARGET_DIRS"][Config.DIR_ASSETS.value]
    dir_draws = lac["TARGET_DIRS"][Config.DIR_DRAWS.value]
    dir_journals = lac["TARGET_DIRS"][Config.DIR_JOURNALS.value]
    dir_pages = lac["TARGET_DIRS"][Config.DIR_PAGES.value]
    dir_whiteboards = lac["TARGET_DIRS"][Config.DIR_WHITEBOARDS.value]
    AssetsDirectory(dir_assets)
    DrawsDirectory(dir_draws)
    JournalsDirectory(dir_journals)
    PagesDirectory(dir_pages)
    WhiteboardsDirectory(dir_whiteboards)
    lac.set_logseq_target_dirs()
    logging.debug("run_app: setup_target_dirs")


def setup_datetime_tokens(token_map: dict[str, str], config: dict[str, str]) -> LogseqJournalFormats:
    """Setup datetime tokens."""
    ljf = LogseqJournalFormats()
    ldtt = LogseqDateTimeTokens(token_map)
    ldtt.set_datetime_token_pattern()
    ldtt.set_journal_py_formatting(config, ljf)
    del ldtt
    logging.debug("run_app: setup_datetime_tokens")
    return ljf


def setup_cache(a: Args) -> tuple[Cache, FileIndex]:
    """Setup cache for the Logseq Analyzer."""
    cache_path = CacheFile().path
    c = Cache(cache_path)
    index = FileIndex()
    if a.graph_cache:
        c.clear()
    else:
        c.clear_deleted_files(index)
    logging.debug("run_app: setup_cache")
    return c, index


def setup_logseq_filename_class(
    lac: LogseqAnalyzerConfig, gc_config: dict[str, str], ljf: LogseqJournalFormats
) -> LogseqFile:
    """Setup the Logseq file class."""
    LogseqFilename.gc_config = gc_config
    LogseqFilename.journal_file_format = ljf.file
    LogseqFilename.journal_page_format = ljf.page
    LogseqFilename.lac_ls_config = lac["LOGSEQ_CONFIG"]
    LogseqFilename.ns_file_sep = lac["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"]
    logging.debug("run_app: setup_logseq_filename_class")


def setup_logseq_graph(index: FileIndex, cache: Cache, target_dirs: set[str]) -> LogseqGraph:
    """Setup the Logseq graph."""
    lg = LogseqGraph()
    lg.process_graph_files(index, cache, GraphDirectory().path, target_dirs)
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
    ln.analyze_ns_queries(index, ContentPatterns.PAGE_REFERENCE)
    ln.detect_non_ns_conflicts(index, graph.dangling_links)
    ln.detect_parent_depth_conflicts()
    logging.debug("run_app: setup_logseq_namespaces")
    return ln


def setup_logseq_journals(graph: LogseqGraph, index: FileIndex, ljf: LogseqJournalFormats) -> LogseqJournals:
    """Setup LogseqJournals."""
    lj = LogseqJournals()
    lj.process_journals_timelines(index, graph.dangling_links, ljf.page)
    logging.debug("run_app: setup_logseq_journals")
    return lj


def setup_logseq_hls_assets(index: FileIndex) -> LogseqAssetsHls:
    """Setup LogseqAssetsHls for HLS assets."""
    lah = LogseqAssetsHls()
    lah.get_asset_files(index)
    lah.convert_names_to_data(index, ContentPatterns.PROPERTY_VALUE)
    lah.check_backlinks()
    logging.debug("run_app: setup_logseq_hls_assets")
    return lah


def setup_logseq_assets(index: FileIndex) -> LogseqAssets:
    """Setup LogseqAssets for handling assets."""
    lsa = LogseqAssets()
    lsa.handle_assets(index)
    logging.debug("run_app: setup_logseq_assets")
    return lsa


def setup_logseq_file_mover(args: Args, unlinked_assets: list[LogseqFile]) -> dict[str, Any]:
    """Setup LogseqFileMover for moving files and directories."""
    dbd = DeleteBakDirectory().path
    bd = BakDirectory().path
    drd = DeleteRecycleDirectory().path
    rd = RecycleDirectory().path
    dad = DeleteAssetsDirectory().path
    moved_files = {}
    moved_files[Moved.ASSETS.value] = handle_move_assets(args.move_unlinked_assets, dad, unlinked_assets)
    moved_files[Moved.BAK.value] = handle_move_directory(args.move_bak, dbd, bd)
    moved_files[Moved.RECYCLE.value] = handle_move_directory(args.move_recycle, drd, rd)
    logging.debug("run_app: setup_logseq_file_mover")
    return moved_files


def get_meta_reports(lg: LogseqGraph, lgc: LogseqGraphConfig, a: Args) -> dict[str, Any]:
    """Get metadata reports from the graph and configuration."""
    index = FileIndex()
    meta_reports = {
        Output.ALL_LINKED_REFERENCES.value: lg.all_linked_references,
        Output.ALL_DANGLING_LINKS.value: lg.all_dangling_links,
        Output.CONFIG_MERGED.value: lgc.config_merged,
        Output.CONFIG_USER.value: lgc.get_user_config(),
        Output.CONFIG_GLOBAL.value: lgc.get_global_config(),
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
        Output.DANGLING_JOURNALS_PAST.value: lj.dangling_journals_dict["past"],
        Output.DANGLING_JOURNALS_FUTURE.value: lj.dangling_journals_dict["future"],
    }


def get_namespace_reports(ln: LogseqNamespaces) -> dict[str, Any]:
    """Get namespace reports from the graph namespaces."""
    logging.debug("run_app: get_namespace_reports")
    return {
        Output.NAMESPACE_DATA.value: ln.structure.data,
        Output.NAMESPACE_PARTS.value: ln.structure.parts,
        Output.UNIQUE_NAMESPACE_PARTS.value: ln.structure.unique_parts,
        Output.NAMESPACE_DETAILS.value: ln.structure.details,
        Output.UNIQUE_NAMESPACES_PER_LEVEL.value: ln.structure.unique_namespaces_per_level,
        Output.NAMESPACE_QUERIES.value: ln.queries,
        Output.NAMESPACE_HIERARCHY.value: ln.structure.tree,
        Output.CONFLICTS_NON_NAMESPACE.value: ln.conflicts.non_namespace,
        Output.CONFLICTS_DANGLING.value: ln.conflicts.dangling,
        Output.CONFLICTS_PARENT_DEPTH.value: ln.conflicts.parent_depth,
        Output.CONFLICTS_PARENT_UNIQUE.value: ln.conflicts.parent_unique,
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


def update_cache(cache: Cache, index: FileIndex) -> None:
    """Update the cache with the current index."""
    cache.cache["index"] = index
    logging.debug("run_app: update_cache")


def write_reports(data_reports: tuple[Any], report_format: str, output_dir_path: Path) -> None:
    """Write reports to the specified output directories."""
    ReportWriter.ext = report_format
    ReportWriter.output_dir = output_dir_path
    for subdir, reports in data_reports:
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logging.debug("run_app: write_reports")


def initialize_configurations(args: Args) -> Configurations:
    """Initialize configurations for the Logseq analyzer."""
    analyzer_config = setup_logseq_analyzer_config(args)
    setup_logseq_paths(analyzer_config)
    graph_config = setup_logseq_graph_config(args, analyzer_config)
    gc_config_merged = graph_config.config_merged
    setup_target_dirs(analyzer_config, gc_config_merged)
    datetime_token_map = analyzer_config["DATETIME_TOKEN_MAP"]
    journal_formats = setup_datetime_tokens(datetime_token_map, gc_config_merged)
    configs = Configurations(analyzer_config, graph_config, journal_formats)
    return configs


def perform_core_analysis(
    args: Args,
    index: FileIndex,
    cache: Cache,
    configs: Configurations,
) -> tuple[tuple[str, Any], ...]:
    """Perform core analysis on the Logseq graph."""
    setup_logseq_filename_class(configs.analyzer, configs.graph.config_merged, configs.journal_formats)
    graph = setup_logseq_graph(index, cache, configs.analyzer.target_dirs)
    summary_files = setup_logseq_file_summarizer(index)
    summary_content = setup_logseq_content_summarizer(index)
    graph_namespaces = setup_logseq_namespaces(graph, index)
    graph_journals = setup_logseq_journals(graph, index, configs.journal_formats)
    hls_assets = setup_logseq_hls_assets(index)
    ls_assets = setup_logseq_assets(index)
    moved_files = setup_logseq_file_mover(args, ls_assets.not_backlinked)
    data_reports = (
        (OutputDir.META.value, get_meta_reports(graph, configs.graph, args)),
        (OutputDir.JOURNALS.value, get_journal_reports(graph_journals)),
        (OutputDir.NAMESPACES.value, get_namespace_reports(graph_namespaces)),
        (OutputDir.MOVED_FILES.value, get_moved_files_reports(moved_files, ls_assets, hls_assets)),
        (OutputDir.SUMMARY_FILES.value, summary_files.subsets),
        (OutputDir.SUMMARY_CONTENT.value, summary_content.subsets),
    )
    return data_reports


def finish_analysis(cache: Cache, index: FileIndex, configs: Configurations) -> None:
    """Finish the analysis by closing the cache and writing the user configuration."""
    update_cache(cache, index)
    path = Path.cwd() / Constants.CONFIG_USER_INI_FILE.value
    if not path.exists():
        path = Path.cwd() / "_internal" / Constants.CONFIG_USER_INI_FILE.value
    UserConfigIniFile(path)
    configs.analyzer.write_to_file(UserConfigIniFile().path)
    cache.close()
    logging.debug("run_app: finish_analysis")


def run_app(**kwargs) -> None:
    """Main function to run the Logseq analyzer."""
    progress = kwargs.get("progress_callback", GUIInstanceDummy())
    if isinstance(progress, GUIInstanceDummy):
        progress = progress.update_progress

    progress(10)
    args = setup_logseq_arguments(**kwargs)

    progress(25)
    log_file = init_logseq_paths()

    progress(40)
    setup_logging(log_file.path)

    progress(55)
    configs = initialize_configurations(args)

    progress(70)
    cache, index = setup_cache(args)

    progress(85)
    data_reports = perform_core_analysis(args, index, cache, configs)

    progress(90)
    write_reports(data_reports, configs.analyzer["ANALYZER"]["REPORT_FORMAT"], OutputDirectory().path)

    progress(95)
    finish_analysis(cache, index, configs)

    progress(100)
