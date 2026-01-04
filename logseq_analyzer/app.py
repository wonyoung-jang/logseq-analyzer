"""Module for main application logic for the Logseq analyzer."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .analysis.assets import LogseqAssets, LogseqAssetsHls
from .analysis.graph import LogseqGraph
from .analysis.index import FileIndex
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .analysis.summarizers import LogseqContentSummarizer, LogseqFileSummarizer
from .config.arguments import Args
from .config.graph_config import (
    ConfigEdns,
    get_default_logseq_config,
    get_edn_from_file,
    get_file_name_format,
    get_page_title_format,
    get_target_dirs,
)
from .io.cache import Cache
from .io.filesystem import (
    AnalyzerDeleteDirs,
    AssetsDirectory,
    BakDirectory,
    CacheFile,
    ConfigFile,
    DrawsDirectory,
    GlobalConfigFile,
    GraphDirectory,
    JournalsDirectory,
    LogFile,
    LogseqAnalyzerDirs,
    LogseqDirectory,
    LogseqGraphDirs,
    OutputDirectory,
    PagesDirectory,
    RecycleDirectory,
    WhiteboardsDirectory,
)
from .io.report_writer import ReportWriter
from .logseq_file.file import LogseqFile, LogseqPath
from .logseq_file.info import JournalFormats
from .logseq_file.stats import LogseqFileName
from .utils.date_utilities import DateUtilities
from .utils.enums import Constant, LogseqGraphStructure, Moved, Output, OutputDir, TargetDir
from .utils.helpers import (
    process_moves,
    yield_asset_paths,
    yield_bak_rec_paths,
)

if TYPE_CHECKING:
    from collections.abc import Generator

log_file = LogFile(Path(Constant.LOG_FILE))
logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
    filemode="w",
    filename=log_file.path,
    force=True,
    format="%(asctime)s - %(levelname)s:%(name)s - %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
logger.info("Logseq Analyzer started.")
logger.debug("Logging initialized to %s", log_file.path)


@dataclass(slots=True)
class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    progress: dict[str, int] = field(default_factory=dict)

    def __repr__(self) -> str:
        """Return a string representation of the dummy GUI instance."""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """Return a string representation of the dummy GUI instance."""
        return f"{self.__class__.__name__}"

    def update_progress(self, percentage: int) -> None:
        """Simulate updating progress in a GUI."""
        logger.info("Updating progress: %d%%", percentage)


def setup_logseq_paths(args: Args) -> tuple[LogseqAnalyzerDirs, ConfigEdns]:
    """Set up Logseq analyzer configuration based on arguments."""
    graph_dirs = setup_graph_dirs(args)
    config_edns = setup_config_edns(args, graph_dirs)
    target_dirs = get_target_dirs(config_edns.config)
    ensure_target_dirs(graph_dirs, target_dirs)
    analyzer_dirs = LogseqAnalyzerDirs(
        graph_dirs=graph_dirs,
        delete_dirs=AnalyzerDeleteDirs(),
        target_dirs=target_dirs,
        output_dir=OutputDirectory(Path(Constant.OUTPUT_DIR)),
    )

    logger.debug("setup_logseq_paths")
    return analyzer_dirs, config_edns


def setup_graph_dirs(args: Args) -> LogseqGraphDirs:
    """Set up the Logseq graph directories."""
    graph_folder_path = Path(args.graph_folder)
    logseq_dir = graph_folder_path / LogseqGraphStructure.LOGSEQ
    bak_dir = logseq_dir / LogseqGraphStructure.BAK
    recycle_dir = logseq_dir / LogseqGraphStructure.RECYCLE
    user_config_file = logseq_dir / LogseqGraphStructure.CONFIG_EDN
    logger.debug("setup_graph_dirs")
    return LogseqGraphDirs(
        graph_dir=GraphDirectory(graph_folder_path),
        logseq_dir=LogseqDirectory(logseq_dir),
        bak_dir=BakDirectory(bak_dir),
        recycle_dir=RecycleDirectory(recycle_dir),
        user_config=ConfigFile(user_config_file),
    )


def setup_config_edns(args: Args, graph_dirs: LogseqGraphDirs) -> ConfigEdns:
    """Set up the configuration EDN files."""
    default_edn = get_default_logseq_config()
    user_config_edn_parsed = get_edn_from_file(graph_dirs.user_config.path)
    user_edn = {}
    if isinstance(user_config_edn_parsed, dict):
        user_edn.update(user_config_edn_parsed)

    global_edn = {}
    if global_config_path := args.global_config:
        graph_dirs.global_config = GlobalConfigFile(Path(global_config_path))
        global_config_edn_parsed = get_edn_from_file(graph_dirs.global_config.path)
        if isinstance(global_config_edn_parsed, dict):
            global_edn.update(global_config_edn_parsed)

    logger.debug("setup_config_edns")
    return ConfigEdns(
        config=default_edn | user_edn | global_edn,
        default_edn=default_edn,
        user_edn=user_edn,
        global_edn=global_edn,
    )


def ensure_target_dirs(graph_dirs: LogseqGraphDirs, target_dirs: dict[str, str]) -> None:
    """Ensure that the target directories exist."""
    graph_folder_path = graph_dirs.graph_dir.path
    AssetsDirectory(graph_folder_path / target_dirs[TargetDir.ASSET])
    DrawsDirectory(graph_folder_path / target_dirs[TargetDir.DRAW])
    JournalsDirectory(graph_folder_path / target_dirs[TargetDir.JOURNAL])
    PagesDirectory(graph_folder_path / target_dirs[TargetDir.PAGE])
    WhiteboardsDirectory(graph_folder_path / target_dirs[TargetDir.WHITEBOARD])


def setup_journal_formats(config_edns: ConfigEdns) -> JournalFormats:
    """Set up journal formats."""
    _tokens = DateUtilities.compile_datetime_tokens()
    journal_file_fmt = get_file_name_format(config_edns.config)
    journal_page_title_fmt = get_page_title_format(config_edns.config)
    logger.debug("setup_journal_formats")
    return JournalFormats(
        file=DateUtilities.cljs_date_to_py(journal_file_fmt, _tokens),
        page=DateUtilities.cljs_date_to_py(journal_page_title_fmt, _tokens),
        page_title=journal_page_title_fmt,
    )


def init_configs(args: Args) -> tuple[LogseqAnalyzerDirs, ConfigEdns, JournalFormats]:
    """Initialize configurations for the Logseq analyzer."""
    analyzer_dirs, config_edns = setup_logseq_paths(args)
    journal_formats = setup_journal_formats(config_edns)
    logger.debug("init_configs")
    return analyzer_dirs, config_edns, journal_formats


def setup_cache() -> tuple[Cache, FileIndex]:
    """Set up cache for the Logseq Analyzer."""
    cache_file = CacheFile(Path(Constant.CACHE_FILE))
    cache = Cache(cache_file.path)
    cache.open()
    index = cache.initialize()
    logger.debug("setup_cache")
    return cache, index


def configure_analyzer_settings(
    args: Args,
    analyzer_dirs: LogseqAnalyzerDirs,
    config_edns: ConfigEdns,
    journal_formats: JournalFormats,
) -> None:
    """Set up the attributes for the LogseqAnalyzer."""
    Cache.configure(args, analyzer_dirs)
    FileIndex.write_graph = args.write_graph
    LogseqJournals.journal_page_format = journal_formats.page
    LogseqPath.configure(analyzer_dirs)
    LogseqFileName.configure(analyzer_dirs, journal_formats, config_edns)
    ReportWriter.configure(args, analyzer_dirs)
    logger.debug("configure_analyzer_settings")


def process_graph(index: FileIndex, cache: Cache) -> None:
    """Process all files in the Logseq graph folder."""
    for path in cache.iter_modified_files():
        file = LogseqFile(path)
        file.process()
        index.add(file)
    logger.debug("process_graph")


def setup_file_mover(args: Args, lsa: LogseqAssets, analyzer_dirs: LogseqAnalyzerDirs) -> dict[str, Any]:
    """Set up LogseqFileMover for moving files and directories."""
    dd = analyzer_dirs.delete_dirs
    gd = analyzer_dirs.graph_dirs
    target_asset = dd.delete_assets_dir.path
    target_bak = dd.delete_bak_dir.path
    target_rec = dd.delete_recycle_dir.path
    asset_paths = yield_asset_paths(lsa.not_backlinked)
    bak_paths = yield_bak_rec_paths(gd.bak_dir.path)
    rec_paths = yield_bak_rec_paths(gd.recycle_dir.path)
    moved_files_report = {
        Moved.ASSETS: process_moves(target_asset, asset_paths, move=args.move_unlinked_assets),
        Moved.BAK: process_moves(target_bak, bak_paths, move=args.move_bak),
        Moved.RECYCLE: process_moves(target_rec, rec_paths, move=args.move_recycle),
    }
    logger.debug("setup_logseq_file_mover")
    return {Output.MOVED_FILES: moved_files_report}


def report_configurations(
    args: Args,
    analyzer_dirs: LogseqAnalyzerDirs,
    config_edns: ConfigEdns,
) -> Generator[tuple[str, Any], None, None]:
    """Yield configuration data reports."""
    yield OutputDir.META, args.report
    yield OutputDir.META, config_edns.report
    yield OutputDir.META, analyzer_dirs.report


def analyze(
    args: Args,
    index: FileIndex,
    analyzer_dirs: LogseqAnalyzerDirs,
) -> Generator[tuple[str, Any], None, None]:
    """Perform core analysis on the Logseq graph."""
    logseq_graph = LogseqGraph(index)
    yield OutputDir.GRAPH, logseq_graph.report

    logseq_namespaces = LogseqNamespaces(index, logseq_graph.dangling_links)
    yield OutputDir.NAMESPACES, logseq_namespaces.report

    logseq_journals = LogseqJournals(index, logseq_graph.dangling_links)
    yield OutputDir.JOURNALS, logseq_journals.report

    logseq_assets_hls = LogseqAssetsHls(index)
    yield OutputDir.MOVED_FILES_HLS_ASSETS, logseq_assets_hls.report

    logseq_assets = LogseqAssets(index)
    yield OutputDir.MOVED_FILES_ASSETS, logseq_assets.report

    moved_files = setup_file_mover(args, logseq_assets, analyzer_dirs)
    yield OutputDir.MOVED_FILES, moved_files

    logseq_file_summarizer = LogseqFileSummarizer(index)
    yield OutputDir.SUMMARY_FILES_GENERAL, logseq_file_summarizer.general
    yield OutputDir.SUMMARY_FILES_FILE, logseq_file_summarizer.filetypes
    yield OutputDir.SUMMARY_FILES_NODE, logseq_file_summarizer.nodetypes
    yield OutputDir.SUMMARY_FILES_EXTENSIONS, logseq_file_summarizer.extensions

    logseq_content_summarizer = LogseqContentSummarizer(index)
    yield OutputDir.SUMMARY_CONTENT, logseq_content_summarizer.report
    yield OutputDir.SUMMARY_CONTENT_INFO, logseq_content_summarizer.size_report
    yield OutputDir.SUMMARY_CONTENT_INFO, logseq_content_summarizer.timestamp_report
    yield OutputDir.SUMMARY_CONTENT_INFO, logseq_content_summarizer.namespace_report
    yield OutputDir.SUMMARY_CONTENT_INFO, logseq_content_summarizer.bullet_report

    yield OutputDir.INDEX, index.report
    logger.debug("analyze")


def write_reports(data_reports: Generator[tuple[str, Any], None, None]) -> None:
    """Write reports to the specified output directories."""
    for subdir, reports in data_reports:
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logger.debug("write_reports")


def run_app(**gui_args: Any) -> None:
    """Run the Logseq analyzer."""
    progress = gui_args.pop("progress_callback", GUIInstanceDummy().update_progress)

    progress(10, "Starting Logseq Analyzer...")
    args = Args()
    if gui_args:
        args.set_gui_args(gui_args)
    else:
        args.set_cli_args()

    progress(30, "Setting up Logseq Analyzer configurations...")
    analyzer_dirs, config_edns, journal_formats = init_configs(args)

    progress(40, "Configure Logseq Analyzer settings...")
    configure_analyzer_settings(args, analyzer_dirs, config_edns, journal_formats)

    progress(50, "Setup cache...")
    cache, index = setup_cache()

    progress(60, "Process Logseq graph...")
    process_graph(index, cache)

    progress(70, "Write meta reports...")
    write_reports(report_configurations(args, analyzer_dirs, config_edns))

    progress(80, "Running core analysis on Logseq graph...")
    write_reports(analyze(args, index, analyzer_dirs))

    progress(90, "Finalizing analysis...")
    cache.close(index)

    progress(100, "Logseq Analyzer completed successfully.")
