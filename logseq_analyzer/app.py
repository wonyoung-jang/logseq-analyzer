"""Module for main application logic for the Logseq analyzer."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.adapter.ednconfig import ConfigEdns, get_edn_from_file
from logseq_analyzer.adapter.filemover import LogseqFileMover
from logseq_analyzer.adapter.filesystem import check_path, read_content
from logseq_analyzer.adapter.reporter import ReportWriter
from logseq_analyzer.domain.enums import Core, FileType, Output, TargetDir
from logseq_analyzer.domain.model import LogseqFile, get_content_data, yield_asset
from logseq_analyzer.domain.patterns import cljs_date_to_py
from logseq_analyzer.service.analysis import LogseqAnalyzer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sized


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogseqFileContext:
    """Class to hold context data for a Logseq file."""

    jrnlfmt_file: str
    jrnlfmt_page: str
    jrnlfmt_page_title: str
    nsfilesep: str


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


def _iter_files(graph: Path, target: set[str]) -> Iterator[Path]:
    """Recursively iterate over files in the root directory."""
    for root, dirs, files in graph.walk():
        if root != graph and not target.isdisjoint(root.parts):
            yield from (root / f for f in files if not f.endswith(".org"))
        elif root != graph:
            dirs.clear()


def get_report(obj: Any) -> list[tuple[str, Sized]]:
    """Generate a report for the given object."""
    return [(k, getattr(obj, k)) for k in obj.__slots__]


def analyze(index: set[LogseqFile], journal_page_fmt: str) -> Iterator[tuple[str, list[tuple[str, Sized]]]]:
    """Perform core analysis on the Logseq graph."""
    analyzer = LogseqAnalyzer(index, journal_page_fmt)
    analyzer.process()
    yield Output.Dir.GRAPH, get_report(analyzer.graph)
    yield Output.Dir.ASSET, get_report(analyzer.asset)
    yield Output.Dir.NAMESPACE, get_report(analyzer.namespace)
    yield Output.Dir.JOURNAL, get_report(analyzer.journal)
    yield Output.Dir.SUMMARY, get_report(analyzer.summary)
    report = []
    report.append(("file", index))
    report.append((Output.File.GRAPH_DATA, {f.name: f.data for f in index}))
    yield Output.Dir.INDEX, report


def move(args: Args, index: set[LogseqFile], paths: dict[str, Path]) -> tuple[str, list[tuple[str, Sized]]]:
    """Handle moving of files based on analysis results."""
    return LogseqFileMover(
        should_move_bak=args.move_bak,
        should_move_recycle=args.move_recycle,
        should_move_unlinked_assets=args.move_unlinked_assets,
        unlinked_assets=set(yield_asset(index, link=False)),
        paths=paths,
    ).report


def _get_day_ordinal(day: int) -> str:
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def _get_name(path: Path, ctx: LogseqFileContext, journal_dir: str) -> str:
    """Process the filename to create a page title."""
    name = path.stem.strip(ctx.nsfilesep)
    if path.parent.name == journal_dir:
        try:
            date_obj: datetime = datetime.strptime(name, ctx.jrnlfmt_file).replace(tzinfo=UTC)
            page_title: str = date_obj.strftime(ctx.jrnlfmt_page)
            if Core.DATE_ORDINAL_SUFFIX in ctx.jrnlfmt_page_title:
                day = str(date_obj.day)
                day_with_ordinal = f"{day}{_get_day_ordinal(date_obj.day)}"
                page_title = page_title.replace(day, day_with_ordinal, 1)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, ctx.jrnlfmt_page, e)
            return name
    return unquote(name).replace(ctx.nsfilesep, Core.NS_SEP)


def _get_filetype(path: Path, target: dict[str, tuple[str, str, str]]) -> str:
    """Determine the file type based on the directory structure."""
    if _result := target.get(path.parent.name):
        return _result[1]
    for k, v in target.items():
        if k in path.parts:
            return v[2]
    return FileType.OTHER


def run_app(arguments: dict, progress_callback: Callable[[int, str], None] | None = None) -> None:
    """Run the Logseq analyzer."""
    _init_logging()
    prog = progress_callback or (lambda p, msg: logger.debug("Progress: %d%% - %s", p, msg))

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
        jrnlfmt_file=cljs_date_to_py(lsconfig.filename_fmt),
        jrnlfmt_page=cljs_date_to_py(lsconfig.pagetitle_fmt),
        jrnlfmt_page_title=lsconfig.pagetitle_fmt,
        nsfilesep=lsconfig.ns_sep,
    )
    logger.info("LogseqFileContext: %s", ctx)

    prog(20, "Setup cache...")
    cache = Cache(path=paths["cache"])
    index = cache.reset() if args.graph_cache else cache.load()

    prog(25, "Process Logseq graph...")
    path_content = (
        (path, read_content(path))
        for path in cache.get_modified(
            _iter_files(
                paths["graph"],
                {dir_name for dir_name, _, _ in target_dirs.values()},
            ),
        )
    )
    for path, content in path_content:
        if has_content := bool(content):
            data, has_backlinks = get_content_data(content)
        else:
            data, has_backlinks = {}, False
        name = _get_name(path, ctx, target_dirs[TargetDir.JOURNAL][0])
        filetype = _get_filetype(path, target_dirs)
        index.add(LogseqFile(path, name, filetype, data, has_content, has_backlinks))

    prog(80, "Running core analysis on Logseq graph...")
    writer = ReportWriter(ext=args.report_format, output_dir=paths["output"])
    for report in analyze(index, ctx.jrnlfmt_page):
        writer.write_report(report)
    writer.write_report(move(args, index, paths))

    prog(95, "Saving index to cache...")
    cache.save(index)

    prog(100, "Logseq Analyzer completed successfully.")
