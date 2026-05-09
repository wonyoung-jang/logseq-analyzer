"""Module for main application logic for the Logseq analyzer."""

import logging
import re
import shutil
from datetime import UTC, datetime
from enum import StrEnum
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any

from logseq_analyzer.analysis.assets import LogseqAssets, LogseqAssetsHls
from logseq_analyzer.analysis.graph import LogseqGraph
from logseq_analyzer.analysis.journals import LogseqJournals
from logseq_analyzer.analysis.namespaces import LogseqNamespaces
from logseq_analyzer.analysis.summarizers import LogseqContentSummarizer, LogseqFileSummarizer
from logseq_analyzer.config.arguments import Args
from logseq_analyzer.config.graph_config import DEFAULT_LOGSEQ_CONFIG, ConfigEdns, get_edn_from_file
from logseq_analyzer.io.cache import Cache
from logseq_analyzer.io.filesystem import (
    AnalyzerDeleteDirs,
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
    LogseqAnalyzerDirs,
    LogseqDirectory,
    LogseqGraphDirs,
    OutputDirectory,
    PagesDirectory,
    RecycleDirectory,
    WhiteboardsDirectory,
)
from logseq_analyzer.io.report_writer import ReportWriter
from logseq_analyzer.logseq_file.file import LogseqFile
from logseq_analyzer.logseq_file.info import JournalFormats, LogseqFileContext
from logseq_analyzer.utils.enums import FileType, Output, OutputDir, TargetDir

if TYPE_CHECKING:
    from collections.abc import Iterator

    from logseq_analyzer.analysis.index import FileIndex


class Constant(StrEnum):
    """Constants used in the Logseq Analyzer."""

    CACHE_FILE = "logseq-analyzer-cache.db"
    LOG_FILE = "logseq_analyzer.log"
    OUTPUT_DIR = "logseq-analyzer-output"
    TO_DELETE_ASSETS_DIR = "to-delete/assets"
    TO_DELETE_BAK_DIR = "to-delete/bak"
    TO_DELETE_DIR = "to-delete"
    TO_DELETE_RECYCLE_DIR = "to-delete/.recycle"


logger = logging.getLogger(__name__)


def _init_logging() -> None:
    """Initialize logging for the Logseq Analyzer."""
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
    logger.info("Logseq Analyzer started.")
    logger.debug("Logging initialized to %s", log_file.path)


DATETIME_TOKEN_MAP: dict[str, str] = {
    "yyyy": "%Y",
    "xxxx": "%Y",
    "yy": "%y",
    "xx": "%y",
    "MMMM": "%B",
    "MMM": "%b",
    "MM": "%m",
    "M": "%#m",
    "dd": "%d",
    "d": "%#d",
    "D": "%j",
    "EEEE": "%A",
    "EEE": "%a",
    "EE": "%a",
    "E": "%a",
    "e": "%u",
    "HH": "%H",
    "H": "%H",
    "hh": "%I",
    "h": "%I",
    "mm": "%M",
    "m": "%#M",
    "ss": "%S",
    "s": "%#S",
    "SSS": "%f",
    "a": "%p",
    "A": "%p",
    "Z": "%z",
    "ZZ": "%z",
}
_DATETIME_TOKEN_PATTERN: re.Pattern = re.compile(
    "|".join(re.escape(str(k)) for k in sorted(DATETIME_TOKEN_MAP.keys(), key=len, reverse=True))
)


def _setup_logseq_paths(args: Args) -> tuple[LogseqAnalyzerDirs, ConfigEdns]:
    """Set up Logseq analyzer configuration based on arguments."""
    graph_dirs = _setup_graph_dirs(args)
    config_edns = _setup_config_edns(args, graph_dirs)
    target_dirs = config_edns.get_target_dirs()
    _graph_dir = graph_dirs.graph_dir.path
    AssetsDirectory(_graph_dir / target_dirs[TargetDir.ASSET])
    DrawsDirectory(_graph_dir / target_dirs[TargetDir.DRAW])
    JournalsDirectory(_graph_dir / target_dirs[TargetDir.JOURNAL])
    PagesDirectory(_graph_dir / target_dirs[TargetDir.PAGE])
    WhiteboardsDirectory(_graph_dir / target_dirs[TargetDir.WHITEBOARD])
    analyzer_dirs = LogseqAnalyzerDirs(
        graph_dirs=graph_dirs,
        delete_dirs=AnalyzerDeleteDirs(
            delete_dir=DeleteDirectory(Path(Constant.TO_DELETE_DIR)),
            delete_bak_dir=DeleteBakDirectory(Path(Constant.TO_DELETE_BAK_DIR)),
            delete_recycle_dir=DeleteRecycleDirectory(Path(Constant.TO_DELETE_RECYCLE_DIR)),
            delete_assets_dir=DeleteAssetsDirectory(Path(Constant.TO_DELETE_ASSETS_DIR)),
        ),
        target_dirs=target_dirs,
        output_dir=OutputDirectory(Path(Constant.OUTPUT_DIR)),
    )
    logger.debug("setup_logseq_paths")
    return analyzer_dirs, config_edns


class LogseqGraphStructure(StrEnum):
    """Logseq graph structure components."""

    BAK = "bak"
    CONFIG_EDN = "config.edn"
    LOGSEQ = "logseq"
    RECYCLE = ".recycle"


def _setup_graph_dirs(args: Args) -> LogseqGraphDirs:
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


def _setup_config_edns(args: Args, graph_dirs: LogseqGraphDirs) -> ConfigEdns:
    """Set up the configuration EDN files."""
    default_edn = DEFAULT_LOGSEQ_CONFIG
    user_config_edn_parsed = get_edn_from_file(graph_dirs.user_config.path)
    user_edn = user_config_edn_parsed if isinstance(user_config_edn_parsed, dict) else {}
    global_edn = {}
    if args.global_config:
        graph_dirs.global_config = GlobalConfigFile(Path(args.global_config))
        parsed = get_edn_from_file(graph_dirs.global_config.path)
        global_edn = parsed if isinstance(parsed, dict) else {}
    logger.debug("setup_config_edns")
    return ConfigEdns(
        config=default_edn | user_edn | global_edn,
        default_edn=default_edn,
        user_edn=user_edn,
        global_edn=global_edn,
    )


def _cljs_date_to_py(cljs_format: str, token_pattern: re.Pattern) -> str:
    """Convert a Clojure-style date format to a Python-style date format."""

    def replace_token(match: re.Match) -> str:
        """Replace a date token with its corresponding Python format."""
        token = match.group(0)
        return DATETIME_TOKEN_MAP.get(token, token)

    return token_pattern.sub(replace_token, cljs_format.replace("o", ""))


def _setup_journal_formats(config_edns: ConfigEdns) -> JournalFormats:
    """Set up journal formats."""
    journal_file_fmt = config_edns.get_file_name_format()
    journal_page_fmt = config_edns.get_page_title_format()
    logger.debug("setup_journal_formats")
    return JournalFormats(
        file=_cljs_date_to_py(journal_file_fmt, _DATETIME_TOKEN_PATTERN),
        page=_cljs_date_to_py(journal_page_fmt, _DATETIME_TOKEN_PATTERN),
        page_title=journal_page_fmt,
    )


def setup_cache(args: Args, analyzer_dirs: LogseqAnalyzerDirs) -> tuple[Cache, FileIndex]:
    """Set up cache for the Logseq Analyzer."""
    cache = Cache(
        path=CacheFile(Path(Constant.CACHE_FILE)).path,
        target_dirs=set(analyzer_dirs.target_dirs.values()),
        graph_dir=analyzer_dirs.graph_dirs.graph_dir.path,
        graph_cache=args.graph_cache,
    )
    cache.open()
    index = cache.initialize()
    logger.debug("setup_cache")
    return cache, index


def _process_moves(target_dir: Path, paths: Iterator[Path], *, move: bool) -> list[str]:
    """Process the moving of files to a specified directory.

    Args:
        target_dir (Path): The directory to move files to.
        paths (Iterator[Path]): An iterator yielding file paths to move.
        move (bool): If True, move the files. If False, simulate the move.

    Returns:
        list[str]: A list of names of the moved files/folders.

    """
    listpaths = list(paths)
    names = [path.name for path in listpaths]
    if not names:
        return names
    if not move:
        return [Moved.SIMULATED_PREFIX, *names]
    for src in listpaths:
        dest = target_dir / src.name
        try:
            shutil.move(src, dest)
            logger.warning("Moved file: %s to %s", src, dest)
        except shutil.Error, OSError:
            logger.exception("Failed to move file: %s to %s", src, dest)
    return names


class Moved(StrEnum):
    """Moved files and directories in the Logseq Analyzer."""

    ASSETS = "assets"
    BAK = "bak"
    RECYCLE = "recycle"
    SIMULATED_PREFIX = "======== Simulated only ========"


def setup_file_mover(args: Args, lsa: LogseqAssets, analyzer_dirs: LogseqAnalyzerDirs) -> dict[str, Any]:
    """Set up LogseqFileMover for moving files and directories."""

    def _yield_asset(unlinked_assets: set[LogseqFile]) -> Iterator[Path]:
        """Yield the file paths of unlinked assets."""
        for asset in unlinked_assets:
            yield asset.path.file

    def _yield_bakrec(source_dir: Path) -> Iterator[Path]:
        """Yield the file paths of bak and recycle directories."""
        for root, dirs, files in Path.walk(source_dir):
            for name in chain(dirs, files):
                yield root / name

    dd = analyzer_dirs.delete_dirs
    gd = analyzer_dirs.graph_dirs
    target_asset = dd.delete_assets_dir.path
    target_bak = dd.delete_bak_dir.path
    target_rec = dd.delete_recycle_dir.path
    asset_paths = _yield_asset(lsa.not_backlinked)
    bak_paths = _yield_bakrec(gd.bak_dir.path)
    rec_paths = _yield_bakrec(gd.recycle_dir.path)
    moved_files_report = {
        Moved.ASSETS: _process_moves(target_asset, asset_paths, move=args.move_unlinked_assets),
        Moved.BAK: _process_moves(target_bak, bak_paths, move=args.move_bak),
        Moved.RECYCLE: _process_moves(target_rec, rec_paths, move=args.move_recycle),
    }
    logger.debug("setup_logseq_file_mover")
    return {Output.MOVED_FILES: moved_files_report}


def report_configurations(
    args: Args, analyzer_dirs: LogseqAnalyzerDirs, config_edns: ConfigEdns
) -> Iterator[tuple[str, Any]]:
    """Yield configuration data reports."""
    yield OutputDir.META, args.report
    yield OutputDir.META, config_edns.report
    yield OutputDir.META, analyzer_dirs.report


def analyze(
    args: Args,
    index: FileIndex,
    analyzer_dirs: LogseqAnalyzerDirs,
    journal_page_fmt: str,
) -> Iterator[tuple[str, Any]]:
    """Perform core analysis on the Logseq graph."""
    logseq_graph = LogseqGraph(index)
    logseq_namespaces = LogseqNamespaces(index, logseq_graph.dangling_links)
    logseq_journals = LogseqJournals(index, logseq_graph.dangling_links, journal_page_fmt)
    logseq_assets_hls = LogseqAssetsHls(index)
    logseq_assets = LogseqAssets(index)
    moved_files = setup_file_mover(args, logseq_assets, analyzer_dirs)
    logseq_file_summarizer = LogseqFileSummarizer(index)
    logseq_content_summarizer = LogseqContentSummarizer(index)
    yield OutputDir.GRAPH, logseq_graph.report
    yield OutputDir.NAMESPACES, logseq_namespaces.report
    yield OutputDir.JOURNALS, logseq_journals.report
    yield OutputDir.MOVED_FILES_HLS_ASSETS, logseq_assets_hls.report
    yield OutputDir.MOVED_FILES_ASSETS, logseq_assets.report
    yield OutputDir.MOVED_FILES, moved_files
    yield from logseq_file_summarizer.report.items()
    yield from logseq_content_summarizer.report.items()
    yield OutputDir.INDEX, index.report
    logger.debug("analyze")


def run_app(**gui_args: Any) -> None:
    """Run the Logseq analyzer."""
    _init_logging()
    progress = gui_args.pop("progress_callback", lambda pct, msg: print(f"{pct}% - {msg}"))
    progress(10, "Starting Logseq Analyzer...")
    args = Args()
    if gui_args:
        args.set_gui_args(gui_args)
    else:
        args.set_cli_args()
    progress(30, "Setting up Logseq Analyzer configurations...")
    analyzer_dirs, config_edns = _setup_logseq_paths(args)
    journal_formats = _setup_journal_formats(config_edns)
    progress(40, "Configure Logseq Analyzer settings...")
    _context = LogseqFileContext(
        now_ts=datetime.now(tz=UTC).timestamp(),
        journal_format=journal_formats,
        ns_file_sep=config_edns.get_ns_sep(),
        journal_dir=analyzer_dirs.target_dirs[TargetDir.JOURNAL],
        graph_path=analyzer_dirs.graph_dirs.graph_dir.path,
        result_map={
            analyzer_dirs.target_dirs[TargetDir.ASSET]: (FileType.ASSET, FileType.SUB_ASSET),
            analyzer_dirs.target_dirs[TargetDir.DRAW]: (FileType.DRAW, FileType.SUB_DRAW),
            analyzer_dirs.target_dirs[TargetDir.JOURNAL]: (FileType.JOURNAL, FileType.SUB_JOURNAL),
            analyzer_dirs.target_dirs[TargetDir.PAGE]: (FileType.PAGE, FileType.SUB_PAGE),
            analyzer_dirs.target_dirs[TargetDir.WHITEBOARD]: (FileType.WHITEBOARD, FileType.SUB_WHITEBOARD),
        },
    )
    progress(50, "Setup cache...")
    cache, index = setup_cache(args, analyzer_dirs)
    index.write_graph = args.write_graph
    progress(60, "Process Logseq graph...")
    for path in cache.iter_modified_files():
        index.add(LogseqFile(path, context=_context))
    progress(70, "Write meta reports...")
    _writer = ReportWriter(
        ext=args.report_format,
        output_dir=analyzer_dirs.output_dir.path,
    )
    _writer.write_reports(report_configurations(args, analyzer_dirs, config_edns))
    progress(80, "Running core analysis on Logseq graph...")
    _analysis = analyze(
        args,
        index,
        analyzer_dirs,
        journal_formats.page,
    )
    _writer.write_reports(_analysis)
    progress(90, "Finalizing analysis...")
    cache.close(index)
    progress(100, "Logseq Analyzer completed successfully.")
