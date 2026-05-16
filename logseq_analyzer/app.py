"""Module for main application logic for the Logseq analyzer."""

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.adapter.ednconfig import ConfigEdns, get_edn_from_file
from logseq_analyzer.adapter.filemover import LogseqFileMover
from logseq_analyzer.adapter.filesystem import check_path
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


class Constant:
    """Constants used in the Logseq Analyzer."""

    class App(StrEnum):
        """Application-level constants."""

        CACHE_FILE = "logseq-analyzer-cache.db"
        LOG_FILE = "logseq_analyzer.log"
        OUTPUT_DIR = "logseq-analyzer-output"
        TO_DELETE_DIR = "to-delete"
        TO_DELETE_ASSETS_DIR = "assets"
        TO_DELETE_BAK_DIR = "bak"
        TO_DELETE_RECYCLE_DIR = ".recycle"

    class Logseq(StrEnum):
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


def _init_logging() -> None:
    """Initialize logging for the Logseq Analyzer."""
    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
        filemode="w",
        filename=Path(Constant.App.LOG_FILE),
        force=True,
        format="%(asctime)s - %(levelname)s:%(name)s - %(message)s",
        level=logging.DEBUG,
    )
    logger.info("Logseq Analyzer started.")


def _get_logseq_config(config_user: Path, config_global: Path | None) -> ConfigEdns:
    """Load and merge user and global configuration EDN files."""
    user_edn = get_edn_from_file(config_user)
    global_edn = {}
    if config_global:
        global_edn_parsed = get_edn_from_file(config_global)
        if isinstance(global_edn_parsed, dict):
            global_edn = global_edn_parsed
    return ConfigEdns(user_edn if isinstance(user_edn, dict) else {}, global_edn)


def _get_paths(args: Args) -> dict[str, Path]:
    """Set up Logseq analyzer configuration based on arguments."""
    graph = Path(args.graph_folder)
    logseq = graph / Constant.Logseq.LOGSEQ
    del_dir = Path(Constant.App.TO_DELETE_DIR)
    paths = {
        "cache": Path(Constant.App.CACHE_FILE),
        "output": Path(Constant.App.OUTPUT_DIR),
        "graph": graph,
        "logseq": logseq,
        "bak": logseq / Constant.Logseq.BAK,
        "recycle": logseq / Constant.Logseq.RECYCLE,
        "config_user": logseq / Constant.Logseq.CONFIG_EDN,
        "del_dir": del_dir,
        "del_bak": del_dir / Constant.App.TO_DELETE_BAK_DIR,
        "del_recycle": del_dir / Constant.App.TO_DELETE_RECYCLE_DIR,
        "del_assets": del_dir / Constant.App.TO_DELETE_ASSETS_DIR,
    }
    if args.global_config:
        paths["config_global"] = Path(args.global_config)
        check_path(paths["config_global"], must_exist=True)
    check_path(paths["cache"], create=False)
    check_path(paths["output"], is_dir=True, clean_on_init=True)
    check_path(paths["graph"], is_dir=True, must_exist=True)
    check_path(paths["logseq"], is_dir=True, must_exist=True)
    check_path(paths["bak"], is_dir=True)
    check_path(paths["recycle"], is_dir=True)
    check_path(paths["config_user"], must_exist=True)
    check_path(paths["del_dir"], is_dir=True)
    check_path(paths["del_bak"], is_dir=True)
    check_path(paths["del_recycle"], is_dir=True)
    check_path(paths["del_assets"], is_dir=True)
    return paths


def _cljs_date_to_py(cljs_format: str) -> str:
    """Convert a Clojure-style date format to a Python-style date format."""

    def _repl(match: re.Match) -> str:
        """Replace a date token with its corresponding Python format."""
        token = match.group(0)
        return _DATETIME_TOKEN_MAP.get(token, token)

    return _DATETIME_TOKEN_PATTERN.sub(_repl, cljs_format.replace("o", ""))


def _iter_files(graph: Path, target: set[str]) -> Iterator[Path]:
    """Recursively iterate over files in the root directory."""
    for root, dirs, files in graph.walk():
        if root == graph:
            continue
        if any(name in target for name in (root.name, root.parent.name)):
            for file in files:
                if Path(file).suffix == ".org":
                    logger.info("Skipping org-mode file %s in %s", file, root)
                    continue
                yield root / file
        else:
            logger.info("Skipping directory %s outside target directories", root)
            dirs.clear()


def analyze(args: Args, index: FileIndex, paths: dict[str, Path], journal_page_fmt: str) -> Iterator[dict]:
    """Perform core analysis on the Logseq graph."""
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
        paths=paths,
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
    paths = _get_paths(args)
    config_edns = _get_logseq_config(paths["config_user"], paths.get("config_global"))
    target_dirs = config_edns.get_target_dirs()
    for dirname, _, _ in target_dirs.values():
        check_path(paths["graph"] / dirname, is_dir=True)
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
        ns_file_sep=config_edns.ns_sep,
        graph_path=paths["graph"],
        target=target_dirs,
    )
    _prog(50, "Setup cache...")
    cache = Cache(path=paths["cache"])
    index = cache.reset() if args.graph_cache else cache.load()
    _prog(60, "Process Logseq graph...")
    _files = _iter_files(paths["graph"], {dir_name for dir_name, _, _ in target_dirs.values()})
    for path in cache.get_modified(_files):
        index.add(LogseqFile(path, ctx=_context))
    _prog(70, "Setup writer...")
    _writer = ReportWriter(ext=args.report_format, output_dir=paths["output"])
    _prog(80, "Running core analysis on Logseq graph...")
    _analysis = analyze(args, index, paths, journal_formats.page)
    _writer.write_reports(_analysis)
    _prog(90, "Saving index to cache...")
    cache.save(index)
    _prog(100, "Logseq Analyzer completed successfully.")
