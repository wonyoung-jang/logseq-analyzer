"""Module for main application logic for the Logseq analyzer."""

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.adapter.ednconfig import DEFAULT_LOGSEQ_CONFIG, ConfigEdns, get_edn_from_file
from logseq_analyzer.adapter.filemover import LogseqFileMover
from logseq_analyzer.adapter.filesystem import File, LogseqAnalyzerDirs
from logseq_analyzer.adapter.reporter import ReportWriter
from logseq_analyzer.domain.model import JournalFormats, LogseqFile, LogseqFileContext
from logseq_analyzer.service.analysis import LogseqAnalyzer
from logseq_analyzer.utils.enums import Output

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from logseq_analyzer.domain.model import FileIndex

logger = logging.getLogger(__name__)

_DATETIME_TOKEN_MAP: dict[str, str] = {
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
    "|".join(re.escape(str(k)) for k in sorted(_DATETIME_TOKEN_MAP.keys(), key=len, reverse=True))
)


class Constant(StrEnum):
    """Constants used in the Logseq Analyzer."""

    CACHE_FILE = "logseq-analyzer-cache.db"
    LOG_FILE = "logseq_analyzer.log"
    OUTPUT_DIR = "logseq-analyzer-output"
    TO_DELETE_ASSETS_DIR = "to-delete/assets"
    TO_DELETE_BAK_DIR = "to-delete/bak"
    TO_DELETE_DIR = "to-delete"
    TO_DELETE_RECYCLE_DIR = "to-delete/.recycle"


class LogseqGraphStructure(StrEnum):
    """Logseq graph structure components."""

    BAK = "bak"
    CONFIG_EDN = "config.edn"
    LOGSEQ = "logseq"
    RECYCLE = ".recycle"


@dataclass(slots=True)
class Args:
    """A class to represent arguments for the Logseq Analyzer."""

    global_config: str = ""
    graph_cache: bool = False
    graph_folder: str = ""
    move_bak: bool = False
    move_recycle: bool = False
    move_unlinked_assets: bool = False
    report_format: str = ".txt"
    write_graph: bool = False

    @property
    def report(self) -> dict:
        """Generate a report of the arguments."""
        return {Output.Dir.META: {Output.File.ARGUMENTS: {k: getattr(self, k) for k in self.__slots__}}}


def _init_logging() -> None:
    """Initialize logging for the Logseq Analyzer."""
    log_file = File(Path(Constant.LOG_FILE))
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


def _setup_logseq_paths(args: Args) -> tuple[LogseqAnalyzerDirs, ConfigEdns]:
    """Set up Logseq analyzer configuration based on arguments."""
    graph_dir = Path(args.graph_folder)
    logseq_dir = graph_dir / LogseqGraphStructure.LOGSEQ
    graph = File(graph_dir, is_dir=True, must_exist=True)
    logseq = File(logseq_dir, is_dir=True, must_exist=True)
    bak = File(logseq_dir / LogseqGraphStructure.BAK, is_dir=True)
    recycle = File(logseq_dir / LogseqGraphStructure.RECYCLE, is_dir=True)
    config_user = File(logseq_dir / LogseqGraphStructure.CONFIG_EDN, must_exist=True)
    user_config_edn_parsed = get_edn_from_file(config_user.path)
    user_edn = user_config_edn_parsed if isinstance(user_config_edn_parsed, dict) else {}
    if args.global_config:
        config_global = File(Path(args.global_config), must_exist=True)
        parsed = get_edn_from_file(config_global.path)
        global_edn = parsed if isinstance(parsed, dict) else {}
    else:
        config_global = None
        global_edn = {}
    config_edns = ConfigEdns(
        config=DEFAULT_LOGSEQ_CONFIG | user_edn | global_edn,
        default_edn=DEFAULT_LOGSEQ_CONFIG,
        user_edn=user_edn,
        global_edn=global_edn,
    )
    target_dirs = config_edns.get_target_dirs()
    for dir_name, _, _ in target_dirs.values():
        File(graph.path / dir_name, is_dir=True)
    analyzer_dirs = LogseqAnalyzerDirs(
        graph=graph,
        logseq=logseq,
        bak=bak,
        recycle=recycle,
        config_user=config_user,
        del_directory=File(Path(Constant.TO_DELETE_DIR), is_dir=True),
        del_bak=File(Path(Constant.TO_DELETE_BAK_DIR), is_dir=True),
        del_recycle=File(Path(Constant.TO_DELETE_RECYCLE_DIR), is_dir=True),
        del_assets=File(Path(Constant.TO_DELETE_ASSETS_DIR), is_dir=True),
        target=target_dirs,
        output=File(Path(Constant.OUTPUT_DIR), is_dir=True, clean_on_init=True),
        config_global=config_global,
    )
    return analyzer_dirs, config_edns


def _cljs_date_to_py(cljs_format: str) -> str:
    """Convert a Clojure-style date format to a Python-style date format."""

    def _repl(match: re.Match) -> str:
        """Replace a date token with its corresponding Python format."""
        token = match.group(0)
        return _DATETIME_TOKEN_MAP.get(token, token)

    return _DATETIME_TOKEN_PATTERN.sub(_repl, cljs_format.replace("o", ""))


def _iter_files(graph_dir: Path, target_dirs: set[str]) -> Iterator[Path]:
    """Recursively iterate over files in the root directory."""
    for root, dirs, files in Path.walk(graph_dir):
        if root == graph_dir:
            continue
        if any(name in target_dirs for name in (root.name, root.parent.name)):
            for file in files:
                if Path(file).suffix == ".org":
                    logger.info("Skipping org-mode file %s in %s", file, root)
                    continue
                yield root / file
        else:
            logger.info("Skipping directory %s outside target directories", root)
            dirs.clear()


def analyze(
    args: Args,
    index: FileIndex,
    analyzer_dirs: LogseqAnalyzerDirs,
    config_edns: ConfigEdns,
    journal_page_fmt: str,
) -> Iterator[dict]:
    """Perform core analysis on the Logseq graph."""
    yield args.report
    yield config_edns.report
    yield analyzer_dirs.report
    analyzer = LogseqAnalyzer(index, journal_page_fmt)
    analyzer.process()
    yield analyzer.graph.report
    yield analyzer.asset.report
    yield analyzer.namespace.report
    yield analyzer.journal.report
    yield analyzer.summary.report
    yield LogseqFileMover(
        should_move_bak=args.move_bak,
        should_move_recycle=args.move_recycle,
        should_move_unlinked_assets=args.move_unlinked_assets,
        unlinked_assets=analyzer.asset.not_backlinked,
        del_assets=analyzer_dirs.del_assets.path,
        del_bak=analyzer_dirs.del_bak.path,
        del_recycle=analyzer_dirs.del_recycle.path,
        bak_dir=analyzer_dirs.bak.path,
        recycle_dir=analyzer_dirs.recycle.path,
    ).report
    idx_report = index.report
    idx_report[Output.Dir.INDEX][Output.File.GRAPH_DATA] = {f.name: f.data for f in index}
    if args.write_graph:
        idx_report[Output.Dir.INDEX][Output.File.GRAPH_CONTENT] = {f.name: f.content for f in index}
        idx_report[Output.Dir.INDEX][Output.File.GRAPH_BULLETS] = {f.name: f.all_bullets for f in index}
    yield idx_report


def run_app(arguments: dict, progress_callback: Callable[[int, str], None] | None = None) -> None:
    """Run the Logseq analyzer."""
    _init_logging()
    _prog = progress_callback or (lambda p, msg: logger.info("Progress: %d%% - %s", p, msg))
    _prog(10, "Starting Logseq Analyzer...")
    args = Args(**arguments)
    _prog(30, "Setting up Logseq Analyzer configurations...")
    analyzer_dirs, config_edns = _setup_logseq_paths(args)
    journal_formats = JournalFormats(
        file=_cljs_date_to_py(config_edns.filename_fmt),
        page=_cljs_date_to_py(config_edns.pagetitle_fmt),
        page_title=config_edns.pagetitle_fmt,
    )
    logger.info("JournalFormats: %s", journal_formats)
    _prog(40, "Configure Logseq Analyzer settings...")
    _context = LogseqFileContext(
        now_ts=datetime.now(tz=UTC).timestamp(),
        journal_format=journal_formats,
        ns_file_sep=config_edns.get_ns_sep(),
        graph_path=analyzer_dirs.graph.path,
        target=analyzer_dirs.target,
    )
    _prog(50, "Setup cache...")
    cache = Cache(path=File(Path(Constant.CACHE_FILE), create=False).path)
    index = cache.reset() if args.graph_cache else cache.load()
    _prog(60, "Process Logseq graph...")
    _files = _iter_files(analyzer_dirs.graph.path, {dir_name for dir_name, _, _ in analyzer_dirs.target.values()})
    for path in cache.get_modified(_files):
        index.add(LogseqFile(path, ctx=_context))
    _prog(70, "Setup writer...")
    _writer = ReportWriter(ext=args.report_format, output_dir=analyzer_dirs.output.path)
    _prog(80, "Running core analysis on Logseq graph...")
    _analysis = analyze(args, index, analyzer_dirs, config_edns, journal_formats.page)
    _writer.write_reports(_analysis)
    _prog(90, "Saving index to cache...")
    cache.save(index)
    _prog(100, "Logseq Analyzer completed successfully.")
