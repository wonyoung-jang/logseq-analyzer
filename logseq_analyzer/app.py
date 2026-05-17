"""Module for main application logic for the Logseq analyzer."""

import logging
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.adapter.ednconfig import ConfigEdns, get_edn_from_file
from logseq_analyzer.adapter.filemover import LogseqFileMover
from logseq_analyzer.adapter.filesystem import check_path
from logseq_analyzer.adapter.reporter import ReportWriter
from logseq_analyzer.domain.enums import Output
from logseq_analyzer.domain.model import JournalFormat, LogseqFile, LogseqFileContext
from logseq_analyzer.service.analysis import LogseqAnalyzer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sized

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
    for root, _, files in graph.walk():
        if root != graph and not target.isdisjoint(root.parts):
            yield from (root / f for f in files if not f.endswith(".org"))


def get_report(subdir: str, obj: Any) -> tuple[str, list[tuple[str, Sized]]]:
    """Generate a report for the given object."""
    return (subdir, [(k, getattr(obj, k)) for k in obj.__slots__])


def analyze(index: FileIndex, journal_page_fmt: str) -> Iterator[tuple[str, list[tuple[str, Sized]]]]:
    """Perform core analysis on the Logseq graph."""
    analyzer = LogseqAnalyzer(index, journal_page_fmt)
    analyzer.process()
    yield get_report(Output.Dir.GRAPH, analyzer.graph)
    yield get_report(Output.Dir.ASSET, analyzer.asset)
    yield get_report(Output.Dir.NAMESPACE, analyzer.namespace)
    yield get_report(Output.Dir.JOURNAL, analyzer.journal)
    yield get_report(Output.Dir.SUMMARY, analyzer.summary)
    subdir, report = get_report(Output.Dir.INDEX, index)
    report.append((Output.File.GRAPH_DATA, {f.name: f.data for f in index}))
    yield (subdir, report)


def move(args: Args, index: FileIndex, paths: dict[str, Path]) -> tuple[str, list[tuple[str, Sized]]]:
    """Handle moving of files based on analysis results."""
    return LogseqFileMover(
        should_move_bak=args.move_bak,
        should_move_recycle=args.move_recycle,
        should_move_unlinked_assets=args.move_unlinked_assets,
        unlinked_assets=set(index.yield_backlinked_assets(backlinked=False)),
        paths=paths,
    ).report


def progress(callback: Callable[[int, str], None] | None = None) -> Callable[[int, str], None]:
    """Update progress through a callback or logging."""
    return callback or (lambda p, msg: logger.debug("Progress: %d%% - %s", p, msg))


def run_app(arguments: dict, progress_callback: Callable[[int, str], None] | None = None) -> None:
    """Run the Logseq analyzer."""
    _init_logging()
    prog = progress(progress_callback)
    prog(5, "Starting Logseq Analyzer...")
    args = Args(**arguments)
    prog(10, "Setting up Logseq Analyzer configurations...")
    paths = _get_paths(args)
    lsconfig = _get_logseq_config(paths["config_user"], paths.get("config_global"))
    target_dirs = lsconfig.get_target_dirs()
    for dirname, _, _ in target_dirs.values():
        check_path(paths["graph"] / dirname, is_dir=True)
    prog(15, "Configure Logseq Analyzer settings...")
    ctx = LogseqFileContext(
        journal_format=JournalFormat(
            file=_cljs_date_to_py(lsconfig.filename_fmt),
            page=_cljs_date_to_py(lsconfig.pagetitle_fmt),
            page_title=lsconfig.pagetitle_fmt,
        ),
        ns_file_sep=lsconfig.ns_sep,
        graph_path=paths["graph"],
        target=target_dirs,
    )
    logger.info("LogseqFileContext: %s", ctx)
    prog(20, "Setup cache...")
    cache = Cache(path=paths["cache"])
    index = cache.reset() if args.graph_cache else cache.load()
    prog(25, "Process Logseq graph...")
    files = _iter_files(paths["graph"], {dir_name for dir_name, _, _ in target_dirs.values()})
    modified_files = list(cache.get_modified(files))
    n_modified = len(modified_files)
    increment = 55 / n_modified if n_modified else 0
    for i, path in enumerate(modified_files, 1):
        index.add(LogseqFile(path, ctx))
        prog(int(25 + i * increment), f"Processing file {i}/{n_modified}: {path.name}")
    prog(80, "Running core analysis on Logseq graph...")
    writer = ReportWriter(ext=args.report_format, output_dir=paths["output"])
    analyses = list(analyze(index, ctx.journal_format.page))
    n_analyses = len(analyses)
    increment = 15 / n_analyses if n_analyses else 0
    for i, report in enumerate(analyses, 1):
        writer.write_report(report)
        prog(int(80 + i * increment), f"Writing report {i}/{n_analyses}: {report[0]}")
    writer.write_report(move(args, index, paths))
    prog(95, "Saving index to cache...")
    cache.save(index)
    prog(100, "Logseq Analyzer completed successfully.")
