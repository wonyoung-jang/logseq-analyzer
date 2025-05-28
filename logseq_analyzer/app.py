"""
This module contains the main application logic for the Logseq analyzer.
"""

import logging
from dataclasses import dataclass
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
from .config.graph_config import (
    LogseqGraphConfig,
    get_file_name_format,
    get_ns_sep,
    get_page_title_format,
    get_target_dirs,
    init_config_edn_from_file,
)
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
from .utils.enums import CacheKeys, Config, Constants, Moved, Output, OutputDir

logger = logging.getLogger(__name__)


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
        logger.info("Updating progress: %d%%", percentage)


@dataclass
class Configurations:
    """Class to hold configurations for the Logseq analyzer."""

    analyzer: LogseqAnalyzerConfig
    graph: LogseqGraphConfig
    journal: LogseqJournalFormats


def init_logseq_paths() -> None:
    """Setup Logseq paths for the analyzer."""
    OutputDirectory(Constants.OUTPUT_DIR.value)
    lf = LogFile(Constants.LOG_FILE.value)
    logging.basicConfig(
        filename=lf.path,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s:%(name)s - %(message)s",
        encoding="utf-8",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    logger.info("Logseq Analyzer started.")
    logger.debug("Logging initialized to %s", lf.path)


def init_configs(args: Args) -> Configurations:
    """Initialize configurations for the Logseq analyzer."""
    ac = setup_logseq_analyzer_config(args)
    setup_logseq_paths(ac)

    gc = setup_logseq_graph_config(args, ac)
    setup_target_dirs(ac, gc)

    jf = setup_datetime_tokens(gc)
    return Configurations(analyzer=ac, graph=gc, journal=jf)


def setup_logseq_analyzer_config(args: Args) -> LogseqAnalyzerConfig:
    """Setup Logseq analyzer configuration based on arguments."""
    path = get_config_ini_path(Constants.CONFIG_INI_FILE.value)
    config_ini_file = ConfigIniFile(path)
    lac = LogseqAnalyzerConfig(config_ini_file.path)
    lac.set_value("ANALYZER", "GRAPH_DIR", args.graph_folder)
    lac.set_value("ANALYZER", "REPORT_FORMAT", args.report_format)
    if args.global_config:
        lac.set_value("ANALYZER", "GLOBAL_CONFIG_FILE", args.global_config)
    logger.debug("run_app: setup_logseq_analyzer_config")
    return lac


def get_config_ini_path(name: str) -> Path:
    """Get the path to the config.ini file."""
    path = Path.cwd() / name
    if not path.exists():
        path = Path.cwd() / "_internal" / name
    return path


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
    logger.debug("run_app: setup_logseq_paths")


def setup_logseq_graph_config(args: Args, lac: LogseqAnalyzerConfig) -> LogseqGraphConfig:
    """Setup Logseq graph configuration based on arguments."""
    lgc = LogseqGraphConfig()
    config_path = lac["ANALYZER"]["USER_CONFIG_FILE"]
    cf = ConfigFile(config_path)
    lgc.user_edn = init_config_edn_from_file(cf.path)
    if args.global_config:
        global_config_path = lac["ANALYZER"]["GLOBAL_CONFIG_FILE"]
        gcf = GlobalConfigFile(global_config_path)
        lgc.global_edn = init_config_edn_from_file(gcf.path)
    lgc.merge()
    logger.debug("run_app: setup_logseq_graph_config")
    return lgc


def setup_target_dirs(lac: LogseqAnalyzerConfig, gc: LogseqGraphConfig) -> None:
    """Setup the target directories for the Logseq analyzer by configuring and validating the necessary paths."""
    target_dirs = get_target_dirs(gc.config)
    lac.set_logseq_config_edn_data(target_dirs)
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
    logger.debug("run_app: setup_target_dirs")


def setup_datetime_tokens(gc: LogseqGraphConfig) -> LogseqJournalFormats:
    """Setup datetime tokens."""
    ldtt = LogseqDateTimeTokens()
    journal_file_format = get_file_name_format(gc.config)
    journal_page_format = get_page_title_format(gc.config)

    ljf = LogseqJournalFormats()
    ljf.file = ldtt.convert_cljs_date_to_py(journal_file_format)
    ljf.page = ldtt.convert_cljs_date_to_py(journal_page_format)
    del ldtt
    logger.debug("run_app: setup_datetime_tokens")
    return ljf


def setup_cache(args: Args) -> tuple[Cache, FileIndex]:
    """Setup cache for the Logseq Analyzer."""
    index = FileIndex()
    cache_path = CacheFile(Constants.CACHE_FILE.value).path
    c = Cache(cache_path)
    c.initialize(args.graph_cache, index)
    logger.debug("run_app: setup_cache")
    return c, index


def perform_core_analysis(
    args: Args,
    index: FileIndex,
    cache: Cache,
    configs: Configurations,
) -> tuple[tuple[str, Any], ...]:
    """Perform core analysis on the Logseq graph."""
    setup_logseq_filename_class(configs)
    process_graph_files(index, cache, configs)
    graph = setup_logseq_graph(index)
    summary_files = setup_logseq_file_summarizer(index)
    summary_content = setup_logseq_content_summarizer(index)
    namespaces = setup_logseq_namespaces(graph, index)
    journals = setup_logseq_journals(graph, index, configs)
    hls_assets = setup_logseq_hls_assets(index)
    ls_assets = setup_logseq_assets(index)
    moved_files = setup_logseq_file_mover(args, ls_assets)
    data_reports = (
        (OutputDir.META.value, args.report),
        (OutputDir.META.value, graph.report),
        (OutputDir.META.value, configs.analyzer.report),
        (OutputDir.META.value, configs.graph.report),
        (OutputDir.META.value, index.report),
        (OutputDir.META.value, index.get_graph_content(args.write_graph)),
        (OutputDir.JOURNALS.value, journals.report),
        (OutputDir.NAMESPACES.value, namespaces.report),
        (OutputDir.MOVED_FILES.value, moved_files),
        (OutputDir.MOVED_FILES.value, ls_assets.report),
        (OutputDir.MOVED_FILES.value, hls_assets.report),
        (OutputDir.SUMMARY_FILES.value, summary_files.report),
        (OutputDir.SUMMARY_CONTENT.value, summary_content.report),
    )
    return data_reports


def setup_logseq_filename_class(c: Configurations) -> LogseqFile:
    """Setup the Logseq file class."""
    LogseqFilename.graph_path = GraphDirectory().path
    LogseqFilename.journal_file_format = c.journal.file
    LogseqFilename.journal_page_format = c.journal.page
    LogseqFilename.journal_page_title_format = get_page_title_format(c.graph.config)
    LogseqFilename.target_dirs = get_target_dirs(c.graph.config)
    LogseqFilename.ns_file_sep = get_ns_sep(c.graph.config)
    logger.debug("run_app: setup_logseq_filename_class")


def setup_logseq_graph(index: FileIndex) -> LogseqGraph:
    """Setup the Logseq graph."""
    lg = LogseqGraph()
    lg.post_processing_content(index)
    lg.process_summary_data(index)
    logger.debug("run_app: setup_logseq_graph")
    return lg


def process_graph_files(index: FileIndex, cache: Cache, c: Configurations) -> None:
    """Process all files in the Logseq graph folder."""
    graph_dir = GraphDirectory().path
    target_dirs = get_target_dirs(c.graph.config)
    target_dirs = set(target_dirs.values())
    for file_path in cache.iter_modified_files(graph_dir, target_dirs):
        file = LogseqFile(file_path)
        file.init_file_data()
        if file.stat.has_content:
            file.process_content_data()
        index.add(file)
    logger.debug("run_app: process_graph_files")


def setup_logseq_file_summarizer(index: FileIndex) -> LogseqFileSummarizer:
    """Setup the Logseq file summarizer."""
    lfs = LogseqFileSummarizer(index)
    lfs.generate_summary()
    logger.debug("run_app: setup_logseq_file_summarizer")
    return lfs


def setup_logseq_content_summarizer(index: FileIndex) -> LogseqContentSummarizer:
    """Setup the Logseq content summarizer."""
    lcs = LogseqContentSummarizer(index)
    lcs.generate_summary()
    logger.debug("run_app: setup_logseq_content_summarizer")
    return lcs


def setup_logseq_namespaces(graph: LogseqGraph, index: FileIndex) -> LogseqNamespaces:
    """Setup LogseqNamespaces."""
    ln = LogseqNamespaces(index)
    ln.init_ns_parts()
    ln.analyze_ns_queries()
    ln.detect_non_ns_conflicts(graph.dangling_links)
    ln.detect_parent_depth_conflicts()
    logger.debug("run_app: setup_logseq_namespaces")
    return ln


def setup_logseq_journals(graph: LogseqGraph, index: FileIndex, c: Configurations) -> LogseqJournals:
    """Setup LogseqJournals."""
    lj = LogseqJournals()
    lj.process_journals_timelines(index, graph.dangling_links, c.journal.page)
    logger.debug("run_app: setup_logseq_journals")
    return lj


def setup_logseq_hls_assets(index: FileIndex) -> LogseqAssetsHls:
    """Setup LogseqAssetsHls for HLS assets."""
    lah = LogseqAssetsHls()
    lah.get_asset_files(index)
    lah.convert_names_to_data(index)
    lah.check_backlinks()
    logger.debug("run_app: setup_logseq_hls_assets")
    return lah


def setup_logseq_assets(index: FileIndex) -> LogseqAssets:
    """Setup LogseqAssets for handling assets."""
    lsa = LogseqAssets()
    lsa.handle_assets(index)
    logger.debug("run_app: setup_logseq_assets")
    return lsa


def setup_logseq_file_mover(args: Args, lsa: LogseqAssets) -> dict[str, Any]:
    """Setup LogseqFileMover for moving files and directories."""
    dbd = DeleteBakDirectory().path
    bd = BakDirectory().path
    drd = DeleteRecycleDirectory().path
    rd = RecycleDirectory().path
    dad = DeleteAssetsDirectory().path
    moved_files = {}
    moved_files[Moved.ASSETS.value] = handle_move_assets(args.move_unlinked_assets, dad, lsa.not_backlinked)
    moved_files[Moved.BAK.value] = handle_move_directory(args.move_bak, dbd, bd)
    moved_files[Moved.RECYCLE.value] = handle_move_directory(args.move_recycle, drd, rd)
    logger.debug("run_app: setup_logseq_file_mover")
    return {Output.MOVED_FILES.value: moved_files}


def write_reports(data_reports: tuple[Any], c: Configurations) -> None:
    """Write reports to the specified output directories."""
    ReportWriter.ext = c.analyzer["ANALYZER"]["REPORT_FORMAT"]
    ReportWriter.output_dir = OutputDirectory().path
    for subdir, reports in data_reports:
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logger.debug("run_app: write_reports")


def finish_analysis(cache: Cache, index: FileIndex, c: Configurations) -> None:
    """Finish the analysis by closing the cache and writing the user configuration."""
    update_cache(cache, index)
    path = get_config_ini_path(Constants.CONFIG_USER_INI_FILE.value)
    UserConfigIniFile(path)
    c.analyzer.write_to_file(UserConfigIniFile().path)
    cache.close()
    logger.debug("run_app: finish_analysis")


def update_cache(cache: Cache, index: FileIndex) -> None:
    """Update the cache with the current index."""
    cache.cache[CacheKeys.INDEX.value] = index
    logger.debug("run_app: update_cache")


def run_app(**kwargs) -> None:
    """Main function to run the Logseq analyzer."""
    progress = kwargs.get("progress_callback", GUIInstanceDummy())
    if isinstance(progress, GUIInstanceDummy):
        progress = progress.update_progress

    progress(10, "Starting Logseq Analyzer...")
    args = Args(**kwargs)

    progress(20, "Initializing Logseq Analyzer paths and configurations...")
    init_logseq_paths()

    progress(30, "Setting up Logseq Analyzer configurations...")
    configs = init_configs(args)

    progress(40, "Setting up Logseq cache...")
    cache, index = setup_cache(args)

    progress(50, "Running core analysis on Logseq graph...")
    data_reports = perform_core_analysis(args, index, cache, configs)

    progress(60, "Writing reports...")
    write_reports(data_reports, configs)

    progress(80, "Finalizing analysis...")
    finish_analysis(cache, index, configs)

    progress(100, "Logseq Analyzer completed successfully.")
