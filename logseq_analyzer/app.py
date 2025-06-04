"""
This module contains the main application logic for the Logseq analyzer.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

from .analysis.assets import LogseqAssets, LogseqAssetsHls
from .analysis.graph import LogseqGraph
from .analysis.index import FileIndex
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .analysis.summarizers import LogseqContentSummarizer, LogseqFileSummarizer
from .config.arguments import Args
from .config.graph_config import (
    get_default_logseq_config,
    get_file_name_format,
    get_ns_sep,
    get_page_title_format,
    get_target_dirs,
    init_config_edn_from_file,
)
from .io.cache import Cache
from .io.filesystem import (
    AssetsDirectory,
    BakDirectory,
    CacheFile,
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
from .logseq_file.file import LogseqFile, LogseqPath
from .utils.enums import Constants, MovedFiles, Output, OutputDir
from .utils.helpers import (
    compile_token_pattern,
    convert_cljs_date_to_py,
    get_token_map,
    process_moves,
    yield_asset_paths,
    yield_bak_rec_paths,
)

log_file = LogFile(Constants.LOG_FILE.value)
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
class LogseqGraphDirs:
    """Directories related to the Logseq graph."""

    graph_dir: GraphDirectory = None
    logseq_dir: LogseqDirectory = None
    bak_dir: BakDirectory = None
    recycle_dir: RecycleDirectory = None
    user_config: ConfigFile = None
    global_config: GlobalConfigFile = None


@dataclass
class AnalyzerDeleteDirs:
    """Directories for deletion operations in the Logseq analyzer."""

    delete_dir: DeleteDirectory = None
    delete_bak_dir: DeleteBakDirectory = None
    delete_recycle_dir: DeleteRecycleDirectory = None
    delete_assets_dir: DeleteAssetsDirectory = None


@dataclass
class ConfigEdns:
    """Configuration EDN files for the Logseq analyzer."""

    config: dict[str, Any] = field(default_factory=dict)
    default_edn: dict[str, Any] = field(default_factory=dict)
    user_edn: dict[str, Any] = field(default_factory=dict)
    global_edn: dict[str, Any] = field(default_factory=dict)


@dataclass
class LogseqAnalyzerDirs:
    """Directories used by the Logseq analyzer."""

    graph_dirs: LogseqGraphDirs = None
    delete_dirs: AnalyzerDeleteDirs = None
    target_dirs: dict[str, str] = field(default_factory=dict)
    output_dir: OutputDirectory = None


@dataclass
class JournalFormats:
    """Formats for Logseq journal files and pages."""

    file_format: str = ""
    page_format: str = ""
    page_title_format: str = ""


def setup_logseq_paths(args: Args) -> tuple[LogseqAnalyzerDirs, ConfigEdns]:
    """Setup Logseq analyzer configuration based on arguments."""
    graph_dirs = setup_graph_dirs(args)
    config_edns = setup_config_edns(args, graph_dirs)
    targets_dirs = get_target_dirs(config_edns.config)
    graph_folder_path = graph_dirs.graph_dir.path
    AssetsDirectory(graph_folder_path / targets_dirs["assets"])
    DrawsDirectory(graph_folder_path / targets_dirs["draws"])
    JournalsDirectory(graph_folder_path / targets_dirs["journals"])
    PagesDirectory(graph_folder_path / targets_dirs["pages"])
    WhiteboardsDirectory(graph_folder_path / targets_dirs["whiteboards"])
    delete_dirs = setup_delete_dirs()
    analyzer_dirs = LogseqAnalyzerDirs(
        graph_dirs=graph_dirs,
        delete_dirs=delete_dirs,
        target_dirs=targets_dirs,
        output_dir=OutputDirectory(Constants.OUTPUT_DIR.value),
    )

    logger.debug("setup_logseq_paths")
    return analyzer_dirs, config_edns


def setup_graph_dirs(args: Args) -> LogseqGraphDirs:
    """Setup the Logseq graph directories."""
    graph_folder_path = Path(args.graph_folder)
    logseq_dir = graph_folder_path / "logseq"
    bak_dir = logseq_dir / "bak"
    recycle_dir = logseq_dir / ".recycle"
    user_config_file = logseq_dir / "config.edn"
    logger.debug("setup_graph_dirs")
    return LogseqGraphDirs(
        graph_dir=GraphDirectory(graph_folder_path),
        logseq_dir=LogseqDirectory(logseq_dir),
        bak_dir=BakDirectory(bak_dir),
        recycle_dir=RecycleDirectory(recycle_dir),
        user_config=ConfigFile(user_config_file),
    )


def setup_config_edns(args: Args, graph_dirs: LogseqGraphDirs) -> ConfigEdns:
    """Setup the configuration EDN files."""
    default_edn = get_default_logseq_config()
    user_edn = init_config_edn_from_file(graph_dirs.user_config.path)
    global_edn = {}
    if global_config_path := args.global_config:
        graph_dirs.global_config = GlobalConfigFile(Path(global_config_path))
        global_edn.update(init_config_edn_from_file(graph_dirs.global_config.path))
    logger.debug("setup_config_edns")
    return ConfigEdns(
        config=default_edn | user_edn | global_edn,
        default_edn=default_edn,
        user_edn=user_edn,
        global_edn=global_edn,
    )


def setup_delete_dirs() -> AnalyzerDeleteDirs:
    """Setup the directories for deletion operations."""
    logger.debug("setup_delete_dirs")
    return AnalyzerDeleteDirs(
        delete_dir=DeleteDirectory(Constants.TO_DELETE_DIR.value),
        delete_bak_dir=DeleteBakDirectory(Constants.TO_DELETE_BAK_DIR.value),
        delete_recycle_dir=DeleteRecycleDirectory(Constants.TO_DELETE_RECYCLE_DIR.value),
        delete_assets_dir=DeleteAssetsDirectory(Constants.TO_DELETE_ASSETS_DIR.value),
    )


def setup_journal_formats(config_edns: ConfigEdns) -> JournalFormats:
    """Setup journal formats."""
    _token_map = get_token_map()
    _token_pattern = compile_token_pattern(_token_map)
    journal_file_fmt = get_file_name_format(config_edns.config)
    journal_page_title_fmt = get_page_title_format(config_edns.config)
    logger.debug("setup_journal_formats")
    return JournalFormats(
        file_format=convert_cljs_date_to_py(journal_file_fmt, _token_map, _token_pattern),
        page_format=convert_cljs_date_to_py(journal_page_title_fmt, _token_map, _token_pattern),
        page_title_format=journal_page_title_fmt,
    )


def init_configs(args: Args) -> tuple[LogseqAnalyzerDirs, ConfigEdns, JournalFormats]:
    """Initialize configurations for the Logseq analyzer."""
    analyzer_dirs, config_edns = setup_logseq_paths(args)
    journal_formats = setup_journal_formats(config_edns)
    logger.debug("init_configs")
    return analyzer_dirs, config_edns, journal_formats


def setup_cache() -> tuple[Cache, FileIndex]:
    """Setup cache for the Logseq Analyzer."""
    cache_file = CacheFile(Constants.CACHE_FILE.value)
    cache = Cache(cache_file.path)
    cache.open()
    index = cache.initialize()
    logger.debug("setup_cache")
    return cache, index


def configure_analyzer_settings(
    args: Args,
    analyzer_dirs: LogseqAnalyzerDirs,
    journal_formats: JournalFormats,
    config_edns: ConfigEdns,
) -> None:
    """Setup the attributes for the LogseqAnalyzer."""
    Cache.target_dirs = set(analyzer_dirs.target_dirs.values())
    Cache.graph_dir = analyzer_dirs.graph_dirs.graph_dir.path
    Cache.graph_cache = args.graph_cache

    FileIndex.write_graph = args.write_graph

    LogseqJournals.journal_page_format = journal_formats.page_format

    LogseqPath.graph_path = analyzer_dirs.graph_dirs.graph_dir.path
    LogseqPath.journal_file_format = journal_formats.file_format
    LogseqPath.journal_page_format = journal_formats.page_format
    LogseqPath.journal_page_title_format = journal_formats.page_title_format
    LogseqPath.target_dirs = analyzer_dirs.target_dirs
    LogseqPath.ns_file_sep = get_ns_sep(config_edns.config)
    LogseqPath.set_result_map()

    ReportWriter.ext = args.report_format
    ReportWriter.output_dir = analyzer_dirs.output_dir.path
    logger.debug("configure_analyzer_settings")


def process_graph(index: FileIndex, cache: Cache) -> None:
    """Process all files in the Logseq graph folder."""
    for path in cache.iter_modified_files():
        file = LogseqFile(path)
        file.process()
        index.add(file)
    logger.debug("process_graph")


def setup_graph(index: FileIndex) -> LogseqGraph:
    """Setup the Logseq graph."""
    lg = LogseqGraph()
    lg.process(index)
    logger.debug("setup_graph")
    return lg


def setup_summarizers(index: FileIndex) -> tuple[LogseqFileSummarizer, LogseqContentSummarizer]:
    """Setup the Logseq summarizers."""
    lfs = LogseqFileSummarizer()
    lfs.process(index)
    lcs = LogseqContentSummarizer()
    lcs.process(index)
    logger.debug("setup_summarizers")
    return lfs, lcs


def setup_namespaces(index: FileIndex, graph: LogseqGraph) -> LogseqNamespaces:
    """Setup LogseqNamespaces."""
    ln = LogseqNamespaces()
    ln.process(index, graph.dangling_links)
    logger.debug("setup_namespaces")
    return ln


def setup_journals(index: FileIndex, graph: LogseqGraph) -> LogseqJournals:
    """Setup LogseqJournals."""
    lj = LogseqJournals()
    lj.process(index, graph.dangling_links)
    logger.debug("setup_journals")
    return lj


def setup_assets(index: FileIndex) -> tuple[LogseqAssets, LogseqAssetsHls]:
    """Setup LogseqAssetsHls for HLS assets."""
    lah = LogseqAssetsHls()
    lah.process(index)
    lsa = LogseqAssets()
    lsa.process(index)
    logger.debug("setup_assets")
    return lsa, lah


def setup_file_mover(args: Args, lsa: LogseqAssets, analyzer_dirs: LogseqAnalyzerDirs) -> dict[str, Any]:
    """Setup LogseqFileMover for moving files and directories."""
    target_asset = analyzer_dirs.delete_dirs.delete_assets_dir.path
    target_bak = analyzer_dirs.delete_dirs.delete_bak_dir.path
    target_rec = analyzer_dirs.delete_dirs.delete_recycle_dir.path
    bak_dir = analyzer_dirs.graph_dirs.bak_dir.path
    rec_dir = analyzer_dirs.graph_dirs.recycle_dir.path
    asset_paths = yield_asset_paths(lsa.not_backlinked)
    bak_paths = yield_bak_rec_paths(bak_dir)
    rec_paths = yield_bak_rec_paths(rec_dir)
    moved_assets = process_moves(args.move_unlinked_assets, target_asset, asset_paths)
    moved_bak = process_moves(args.move_bak, target_bak, bak_paths)
    moved_rec = process_moves(args.move_recycle, target_rec, rec_paths)
    moved_files_report = {
        MovedFiles.ASSETS.value: moved_assets,
        MovedFiles.BAK.value: moved_bak,
        MovedFiles.RECYCLE.value: moved_rec,
    }
    logger.debug("setup_logseq_file_mover")
    return {Output.MOVED_FILES.value: moved_files_report}


def analyze(
    args: Args,
    cache: Cache,
    index: FileIndex,
    analyzer_dirs: LogseqAnalyzerDirs,
) -> Generator[tuple[str, Any], None, None]:
    """Perform core analysis on the Logseq graph."""
    yield (OutputDir.META.value, args.report)

    process_graph(index, cache)

    graph = setup_graph(index)
    yield (OutputDir.GRAPH.value, graph.report)
    yield (OutputDir.INDEX.value, index.report)

    namespaces = setup_namespaces(index, graph)
    yield (OutputDir.NAMESPACES.value, namespaces.report)

    journals = setup_journals(index, graph)
    yield (OutputDir.JOURNALS.value, journals.report)

    ls_assets, hls_assets = setup_assets(index)
    yield (OutputDir.MOVED_FILES_ASSETS.value, ls_assets.report)
    yield (OutputDir.MOVED_FILES_HLS_ASSETS.value, hls_assets.report)

    moved_files = setup_file_mover(args, ls_assets, analyzer_dirs)
    yield (OutputDir.MOVED_FILES.value, moved_files)

    summary_files, summary_content = setup_summarizers(index)
    yield (OutputDir.SUMMARY_FILES_GENERAL.value, summary_files.general)
    yield (OutputDir.SUMMARY_FILES_FILE.value, summary_files.filetypes)
    yield (OutputDir.SUMMARY_FILES_NODE.value, summary_files.nodetypes)
    yield (OutputDir.SUMMARY_FILES_EXTENSIONS.value, summary_files.extensions)
    yield (OutputDir.SUMMARY_CONTENT.value, summary_content.report)
    logger.debug("analyze")


def write_reports(data_reports: Generator[tuple[str, Any], None, None]) -> None:
    """Write reports to the specified output directories."""
    for subdir, reports in data_reports:
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logger.debug("write_reports")


def close_cache(cache: Cache, index: FileIndex) -> None:
    """Finish the analysis by closing the cache and writing the user configuration."""
    cache.close(index)
    logger.debug("close_cache")


def run_app(**gui_args) -> None:
    """Main function to run the Logseq analyzer."""
    progress = gui_args.pop("progress_callback", GUIInstanceDummy().update_progress)

    progress(10, "Starting Logseq Analyzer...")
    args = Args(**gui_args)

    progress(30, "Setting up Logseq Analyzer configurations...")
    analyzer_dirs, config_edns, journal_formats = init_configs(args)

    progress(40, "Configure Logseq Analyzer settings...")
    configure_analyzer_settings(args, analyzer_dirs, journal_formats, config_edns)

    progress(50, "Setup cache...")
    cache, index = setup_cache()

    progress(60, "Running core analysis on Logseq graph...")
    data_reports = analyze(args, cache, index, analyzer_dirs)

    progress(70, "Writing reports...")
    write_reports(data_reports)

    progress(80, "Finalizing analysis...")
    close_cache(cache, index)

    progress(100, "Logseq Analyzer completed successfully.")
