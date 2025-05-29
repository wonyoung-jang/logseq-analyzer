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
from .config.datetime_tokens import (
    compile_token_pattern,
    convert_cljs_date_to_py,
    get_token_map,
)
from .config.graph_config import (
    get_default_logseq_config,
    get_file_name_format,
    get_ns_sep,
    get_page_title_format,
    get_target_dirs,
    init_config_edn_from_file,
)
from .io.cache import Cache
from .io.file_mover import handle_move_assets, handle_move_directory
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
from .logseq_file.file import LogseqFile
from .logseq_file.name import LogseqFilename
from .utils.enums import CacheKeys, Constants, Moved, Output, OutputDir

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

    graph: dict[str, Any] = field(default_factory=dict)
    user_edn: dict[str, Any] = field(default_factory=dict)
    global_edn: dict[str, Any] = field(default_factory=dict)
    journal_file_fmt: str = ""
    journal_page_fmt: str = ""


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
    setup_logseq_paths(args)
    gc, user_edn, global_edn = setup_logseq_graph_config(args)
    setup_target_dirs(gc)
    journal_file_fmt, journal_page_fmt = setup_journal_formats(gc)
    return Configurations(gc, user_edn, global_edn, journal_file_fmt, journal_page_fmt)


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
    logger.debug("run_app: setup_logseq_paths")


def setup_logseq_graph_config(args: Args) -> tuple[dict, dict, dict]:
    """Setup Logseq graph configuration based on arguments."""
    config = get_default_logseq_config()
    user_edn = init_config_edn_from_file(ConfigFile().path)
    global_edn = {}
    if args.global_config:
        global_config_path = Path(args.global_config)
        global_config_file = GlobalConfigFile(global_config_path)
        gc_file_path = global_config_file.path
        global_edn = init_config_edn_from_file(gc_file_path)
    config.update(user_edn)
    config.update(global_edn)
    logger.debug("run_app: setup_logseq_graph_config")
    return config, user_edn, global_edn


def setup_target_dirs(gc: dict[str, Any]) -> None:
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
    logger.debug("run_app: setup_target_dirs")


def setup_journal_formats(gc: dict[str, Any]) -> tuple[str, str]:
    """Setup journal formats."""
    token_map = get_token_map()
    token_pattern = compile_token_pattern(token_map)

    journal_file_fmt = get_file_name_format(gc)
    journal_file_fmt = convert_cljs_date_to_py(journal_file_fmt, token_map, token_pattern)

    journal_page_fmt = get_page_title_format(gc)
    journal_page_fmt = convert_cljs_date_to_py(journal_page_fmt, token_map, token_pattern)

    logger.debug("run_app: setup_journal_formats")
    return journal_file_fmt, journal_page_fmt


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
    summary_files, summary_content = setup_logseq_summarizers(index)
    namespaces = setup_logseq_namespaces(graph, index)
    journals = setup_logseq_journals(graph, index, configs)
    ls_assets, hls_assets = setup_logseq_assets(index)
    moved_files = setup_logseq_file_mover(args, ls_assets)
    data_reports = (
        (OutputDir.META.value, args.report),
        # (OutputDir.META.value, configs.graph),
        (OutputDir.GRAPH.value, graph.report),
        (OutputDir.INDEX.value, index.report),
        (OutputDir.INDEX.value, index.get_graph_content(args.write_graph)),
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
    graph_config = c.graph
    LogseqFilename.graph_path = GraphDirectory().path
    LogseqFilename.journal_file_format = c.journal_file_fmt
    LogseqFilename.journal_page_format = c.journal_page_fmt
    LogseqFilename.journal_page_title_format = get_page_title_format(graph_config)
    LogseqFilename.target_dirs = get_target_dirs(graph_config)
    LogseqFilename.ns_file_sep = get_ns_sep(graph_config)
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
    target_dirs = get_target_dirs(c.graph)
    target_dirs = set(target_dirs.values())
    for file_path in cache.iter_modified_files(graph_dir, target_dirs):
        file = LogseqFile(file_path)
        file.init_file_data()
        if file.stat.has_content:
            file.process_content_data()
        index.add(file)
    logger.debug("run_app: process_graph_files")


def setup_logseq_summarizers(index: FileIndex) -> tuple[LogseqFileSummarizer, LogseqContentSummarizer]:
    """Setup the Logseq summarizers."""
    lfs = LogseqFileSummarizer()
    lfs.generate_summary(index)
    lcs = LogseqContentSummarizer()
    lcs.generate_summary(index)
    logger.debug("run_app: setup_logseq_summarizers")
    return lfs, lcs


def setup_logseq_namespaces(graph: LogseqGraph, index: FileIndex) -> LogseqNamespaces:
    """Setup LogseqNamespaces."""
    ln = LogseqNamespaces()
    ln.init_ns_parts(index)
    ln.analyze_ns_queries(index)
    ln.detect_non_ns_conflicts(index, graph.dangling_links)
    ln.detect_parent_depth_conflicts()
    logger.debug("run_app: setup_logseq_namespaces")
    return ln


def setup_logseq_journals(graph: LogseqGraph, index: FileIndex, c: Configurations) -> LogseqJournals:
    """Setup LogseqJournals."""
    lj = LogseqJournals()
    lj.process_journals_timelines(index, graph.dangling_links, c.journal_page_fmt)
    logger.debug("run_app: setup_logseq_journals")
    return lj


def setup_logseq_assets(index: FileIndex) -> tuple[LogseqAssets, LogseqAssetsHls]:
    """Setup LogseqAssetsHls for HLS assets."""
    lah = LogseqAssetsHls()
    lah.get_asset_files(index)
    lah.convert_names_to_data(index)
    lah.check_backlinks()
    lsa = LogseqAssets()
    lsa.handle_assets(index)
    logger.debug("run_app: setup_logseq_assets")
    return lsa, lah


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


def write_reports(data_reports: tuple[Any], args: Args) -> None:
    """Write reports to the specified output directories."""
    ReportWriter.ext = args.report_format
    ReportWriter.output_dir = OutputDirectory().path
    for subdir, reports in data_reports:
        for prefix, data in reports.items():
            ReportWriter(prefix, data, subdir).write()
    logger.debug("run_app: write_reports")


def finish_analysis(cache: Cache, index: FileIndex) -> None:
    """Finish the analysis by closing the cache and writing the user configuration."""
    cache.cache[CacheKeys.INDEX.value] = index
    cache.close()
    logger.debug("run_app: finish_analysis")


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
    write_reports(data_reports, args)

    progress(80, "Finalizing analysis...")
    finish_analysis(cache, index)

    progress(100, "Logseq Analyzer completed successfully.")
