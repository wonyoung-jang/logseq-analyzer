"""Module for main application logic for the Logseq analyzer."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.adapter.ednconfig import LogseqConfig, config_from_path
from logseq_analyzer.adapter.filesystem import (
    check_path,
    determine_move,
    get_paths,
    move_files,
    read_content,
    walk_file,
    walk_filter,
)
from logseq_analyzer.adapter.reporter import ReportWriter
from logseq_analyzer.domain.enums import BACKLINK_CRITERIA, FileType, Output
from logseq_analyzer.domain.model import LogseqFile, get_data, yield_asset
from logseq_analyzer.service.analysis import LogseqAnalyzer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sized


logger = logging.getLogger(__name__)


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


@cache
def _get_day_ordinal(day: int) -> str:
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")


def _get_name(path: Path, lsconfig: LogseqConfig) -> str:
    """Process the filename to create a page title."""
    name = path.stem.strip(lsconfig.ns_sep)
    if path.parent.name == lsconfig.dir_journal:
        try:
            date_obj: datetime = datetime.strptime(name, lsconfig.jrnlfmt_file).replace(tzinfo=UTC)
            page_title: str = date_obj.strftime(lsconfig.jrnlfmt_page)
            if "o" in lsconfig.pagetitle_fmt:
                day = str(date_obj.day)
                day_with_ordinal = f"{day}{_get_day_ordinal(date_obj.day)}"
                page_title = page_title.replace(day, day_with_ordinal, 1)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, lsconfig.jrnlfmt_page, e)
            return name
    return unquote(name).replace(lsconfig.ns_sep, "/")


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
    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
        filemode="w",
        filename=Path("logseq_analyzer.log"),
        force=True,
        format="%(asctime)s - %(levelname)s:%(name)s - %(message)s",
        level=logging.DEBUG,
    )
    prog = progress_callback or (lambda p, msg: logger.debug("Progress: %d%% - %s", p, msg))
    prog(0, "Logseq Analyzer started...")

    prog(10, "Building arguments...")
    args = Args(**arguments)

    prog(20, "Setting up Logseq Analyzer configurations...")
    paths = get_paths(args.graph_folder, args.global_config)
    lsconfig = LogseqConfig.from_config(config_from_path(paths["config_user"], paths.get("config_global")))
    target = lsconfig.target_dirs
    target_dir = {d[0] for d in target.values()}
    for dirname in target_dir:
        check_path(paths["graph"] / dirname, is_dir=True)

    prog(30, "Setup cache...")
    graph_cache = Cache(path=paths["cache"])
    index = graph_cache.reset() if args.graph_cache else graph_cache.load()

    prog(40, "Process Logseq graph...")
    path_content = ((p, read_content(p)) for p in graph_cache.get_modified(walk_filter(paths["graph"], target_dir)))
    for path, content in path_content:
        data = {k: v for k, v in get_data(content) if v} if (has_content := bool(content)) else {}
        name = _get_name(path, lsconfig)
        is_ns = "/" in name
        ns_part = name.split("/")
        index.add(
            LogseqFile(
                path=path,
                name=name,
                filetype=_get_filetype(path, target),
                has_content=has_content,
                has_backlinks=not BACKLINK_CRITERIA.isdisjoint(data.keys()),
                is_hls=name.startswith("hls__"),
                is_ns=is_ns,
                ns_root=ns_part[0] if is_ns else "",
                ns_parent=name.rsplit("/", 1)[0] if is_ns else "",
                ns_part=ns_part,
                data=data,
            )
        )

    prog(70, "Running core analysis on Logseq graph...")
    writer = ReportWriter(ext=args.report_format, output_dir=paths["output"])
    for report in analyze(index, lsconfig.jrnlfmt_page):
        writer.write_report(report)

    prog(80, "Moving files...")
    mover_config = {
        "unlinked_asset": (
            {a.path for a in yield_asset(index, link=False)},
            paths["del_assets"],
            args.move_unlinked_assets,
        ),
        "bak": (set(walk_file(paths["bak"])), paths["del_bak"], args.move_bak),
        "recycle": (set(walk_file(paths["recycle"])), paths["del_recycle"], args.move_recycle),
    }
    moved = {}
    for k, v in mover_config.items():
        files, dest, should_move = v
        if should_move:
            moved[k] = list(move_files(determine_move(files, dest)))
        else:
            moved[f"{k} (simulated)"] = [f.name for f in files]
    writer.write_report((Output.Dir.MOVED, [(Output.File.MOVED, moved)]))

    prog(90, "Saving index to cache...")
    graph_cache.save(index)

    prog(100, "Logseq Analyzer completed successfully.")
