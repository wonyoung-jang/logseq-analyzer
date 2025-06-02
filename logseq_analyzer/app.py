"""
This module contains the main application logic for the Logseq analyzer.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .analysis.assets import LogseqAssets, LogseqAssetsHls
from .analysis.graph import LogseqGraph
from .analysis.index import FileIndex
from .analysis.journals import LogseqJournals
from .analysis.namespaces import LogseqNamespaces
from .analysis.summary_content import LogseqContentSummarizer
from .analysis.summary_files import LogseqFileSummarizer
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
from .utils.enums import CacheKeys, Constants, MovedFiles, Output, OutputDir
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
class Configurations:
    """Class to hold configurations for the Logseq analyzer."""

    config: dict[str, Any] = field(default_factory=dict)
    user_edn: dict[str, Any] = field(default_factory=dict)
    global_edn: dict[str, Any] = field(default_factory=dict)
    journal_file_format: str = ""
    journal_page_format: str = ""
    journal_page_title_format: str = ""
    target_dirs: dict[str, str] = field(default_factory=dict)

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the configurations."""
        journal_formats = {
            Output.CONFIG_JOURNAL_FMT_FILE.value: self.journal_file_format,
            Output.CONFIG_JOURNAL_FMT_PAGE.value: self.journal_page_format,
            Output.CONFIG_JOURNAL_FMT_PAGE_TITLE.value: self.journal_page_title_format,
        }
        return {
            Output.CONFIG_EDN.value: self.config,
            Output.CONFIG_EDN_USER.value: self.user_edn,
            Output.CONFIG_EDN_GLOBAL.value: self.global_edn,
            Output.CONFIG_TARGET_DIRS.value: self.target_dirs,
            Output.CONFIG_JOURNAL_FORMATS.value: journal_formats,
        }


def setup_logseq_paths(args: Args) -> None:
    """Setup Logseq analyzer configuration based on arguments."""
    graph_folder_path = Path(args.graph_folder)
    logseq_dir = graph_folder_path / "logseq"
    bak_dir = logseq_dir / "bak"
    recycle_dir = logseq_dir / ".recycle"
    user_config_file = logseq_dir / "config.edn"
    GraphDirectory(graph_folder_path)
    LogseqDirectory(logseq_dir)
    BakDirectory(bak_dir)
    RecycleDirectory(recycle_dir)
    ConfigFile(user_config_file)
    delete_dir = Constants.TO_DELETE_DIR.value
    delete_bak_dir = Constants.TO_DELETE_BAK_DIR.value
    delete_recycle_dir = Constants.TO_DELETE_RECYCLE_DIR.value
    delete_assets_dir = Constants.TO_DELETE_ASSETS_DIR.value
    DeleteDirectory(delete_dir)
    DeleteBakDirectory(delete_bak_dir)
    DeleteRecycleDirectory(delete_recycle_dir)
    DeleteAssetsDirectory(delete_assets_dir)
    logger.debug("setup_logseq_paths")


def setup_logseq_graph_config(args: Args) -> tuple[dict, dict, dict]:
    """Setup Logseq graph configuration based on arguments."""
    config = get_default_logseq_config()
    cf = ConfigFile()
    user_edn = init_config_edn_from_file(cf.path)
    global_edn = {}
    if args.global_config:
        global_config_path = Path(args.global_config)
        global_config_file = GlobalConfigFile(global_config_path)
        gc_file_path = global_config_file.path
        global_edn = init_config_edn_from_file(gc_file_path)
    config.update(user_edn)
    config.update(global_edn)
    logger.debug("setup_logseq_graph_config")
    return config, user_edn, global_edn


def setup_target_dirs(gc: dict[str, Any]) -> dict[str, str]:
    """Setup the target directories for the Logseq analyzer by configuring and validating the necessary paths."""
    graph_path = GraphDirectory().path
    target_dirs = get_target_dirs(gc)
    dir_assets = graph_path / target_dirs["assets"]
    dir_draws = graph_path / target_dirs["draws"]
    dir_journals = graph_path / target_dirs["journals"]
    dir_pages = graph_path / target_dirs["pages"]
    dir_whiteboards = graph_path / target_dirs["whiteboards"]
    AssetsDirectory(dir_assets)
    DrawsDirectory(dir_draws)
    JournalsDirectory(dir_journals)
    PagesDirectory(dir_pages)
    WhiteboardsDirectory(dir_whiteboards)
    logger.debug("setup_target_dirs")
    return target_dirs


def setup_journal_formats(gc: dict[str, Any]) -> tuple[str, str]:
    """Setup journal formats."""
    token_map = get_token_map()
    token_pattern = compile_token_pattern(token_map)
    journal_file_fmt = get_file_name_format(gc)
    journal_file_fmt = convert_cljs_date_to_py(journal_file_fmt, token_map, token_pattern)
    journal_page_title_fmt = get_page_title_format(gc)
    journal_page_fmt = convert_cljs_date_to_py(journal_page_title_fmt, token_map, token_pattern)
    logger.debug("setup_journal_formats")
    return journal_file_fmt, journal_page_fmt, journal_page_title_fmt


def init_configs(args: Args) -> Configurations:
    """Initialize configurations for the Logseq analyzer."""
    setup_logseq_paths(args)
    gc, user_edn, global_edn = setup_logseq_graph_config(args)
    target_dirs = setup_target_dirs(gc)
    journal_file_fmt, journal_page_fmt, journal_page_title_fmt = setup_journal_formats(gc)
    logger.debug("init_configs")
    return Configurations(
        gc, user_edn, global_edn, journal_file_fmt, journal_page_fmt, journal_page_title_fmt, target_dirs
    )


def setup_cache(args: Args) -> tuple[Cache, FileIndex]:
    """Setup cache for the Logseq Analyzer."""
    index = FileIndex()
    cf = CacheFile(Constants.CACHE_FILE.value)
    cache = Cache(cf.path)
    cache.open(protocol=5)
    cache.initialize(args.graph_cache, index)
    logger.debug("setup_cache")
    return cache, index


def configure_analyzer_settings(args: Args, c: Configurations) -> None:
    """Setup the attributes for the LogseqAnalyzer."""
    graph_dir = GraphDirectory()
    output_dir = OutputDirectory()
    LogseqJournals.journal_page_format = c.journal_page_format
    Cache.graph_dir = graph_dir.path
    Cache.target_dirs = set(c.target_dirs.values())
    LogseqPath.graph_path = graph_dir.path
    LogseqPath.journal_file_format = c.journal_file_format
    LogseqPath.journal_page_format = c.journal_page_format
    LogseqPath.journal_page_title_format = c.journal_page_title_format
    LogseqPath.target_dirs = c.target_dirs
    LogseqPath.ns_file_sep = get_ns_sep(c.config)
    LogseqPath.set_result_map()
    ReportWriter.ext = args.report_format
    ReportWriter.output_dir = output_dir.path
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


def setup_namespaces(graph: LogseqGraph, index: FileIndex) -> LogseqNamespaces:
    """Setup LogseqNamespaces."""
    ln = LogseqNamespaces()
    ln.process(index, graph.dangling_links)
    logger.debug("setup_namespaces")
    return ln


def setup_journals(graph: LogseqGraph, index: FileIndex) -> LogseqJournals:
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


def setup_file_mover(args: Args, lsa: LogseqAssets) -> dict[str, Any]:
    """Setup LogseqFileMover for moving files and directories."""
    target_asset = DeleteAssetsDirectory()
    target_bak = DeleteBakDirectory()
    target_rec = DeleteRecycleDirectory()
    bak_dir = BakDirectory()
    rec_dir = RecycleDirectory()
    asset_paths = yield_asset_paths(lsa.not_backlinked)
    bak_paths = yield_bak_rec_paths(bak_dir.path)
    rec_paths = yield_bak_rec_paths(rec_dir.path)
    moved_assets = process_moves(args.move_unlinked_assets, target_asset.path, asset_paths)
    moved_bak = process_moves(args.move_bak, target_bak.path, bak_paths)
    moved_rec = process_moves(args.move_recycle, target_rec.path, rec_paths)
    moved_files_report = {
        MovedFiles.ASSETS.value: moved_assets,
        MovedFiles.BAK.value: moved_bak,
        MovedFiles.RECYCLE.value: moved_rec,
    }
    logger.debug("setup_logseq_file_mover")
    return {Output.MOVED_FILES.value: moved_files_report}


def analyze(args: Args, configs: Configurations, cache: Cache, index: FileIndex) -> tuple:
    """Perform core analysis on the Logseq graph."""
    process_graph(index, cache)
    graph = setup_graph(index)
    namespaces = setup_namespaces(graph, index)
    journals = setup_journals(graph, index)
    ls_assets, hls_assets = setup_assets(index)
    moved_files = setup_file_mover(args, ls_assets)
    summary_files, summary_content = setup_summarizers(index)
    logger.debug("analyze")
    return (
        (OutputDir.META.value, args.report),
        (OutputDir.META.value, configs.report),
        (OutputDir.GRAPH.value, graph.report),
        (OutputDir.INDEX.value, index.report),
        (OutputDir.INDEX.value, index.get_graph_content(args.write_graph)),
        (OutputDir.JOURNALS.value, journals.report),
        (OutputDir.NAMESPACES.value, namespaces.report),
        (OutputDir.MOVED_FILES.value, moved_files),
        (OutputDir.MOVED_FILES_ASSETS.value, ls_assets.report),
        (OutputDir.MOVED_FILES_HLS_ASSETS.value, hls_assets.report),
        (OutputDir.SUMMARY_FILES_GENERAL.value, summary_files.general),
        (OutputDir.SUMMARY_FILES_FILE.value, summary_files.filetypes),
        (OutputDir.SUMMARY_FILES_NODE.value, summary_files.nodetypes),
        (OutputDir.SUMMARY_FILES_EXTENSIONS.value, summary_files.extensions),
        (OutputDir.SUMMARY_CONTENT.value, summary_content.report),
    )


def write_reports(data_reports: tuple[Any]) -> None:
    """Write reports to the specified output directories."""
    for subdir, reports in data_reports:
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logger.debug("write_reports")


def close_cache(cache: Cache, index: FileIndex) -> None:
    """Finish the analysis by closing the cache and writing the user configuration."""
    cache.cache[CacheKeys.INDEX.value] = index
    cache.close()
    logger.debug("close_cache")


def run_app(**kwargs) -> None:
    """Main function to run the Logseq analyzer."""
    progress = kwargs.pop("progress_callback", GUIInstanceDummy())
    if isinstance(progress, GUIInstanceDummy):
        progress = progress.update_progress

    progress(10, "Starting Logseq Analyzer...")
    args = Args(**kwargs)

    progress(20, "Initializing Logseq Analyzer paths and configurations...")
    OutputDirectory(Constants.OUTPUT_DIR.value)

    progress(30, "Setting up Logseq Analyzer configurations...")
    configs = init_configs(args)

    progress(40, "Setting up Logseq cache...")
    cache, index = setup_cache(args)

    progress(50, "Setup class attributes...")
    configure_analyzer_settings(args, configs)

    progress(60, "Running core analysis on Logseq graph...")
    data_reports = analyze(args, configs, cache, index)

    progress(70, "Writing reports...")
    write_reports(data_reports)

    progress(80, "Finalizing analysis...")
    close_cache(cache, index)

    progress(100, "Logseq Analyzer completed successfully.")
