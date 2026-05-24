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
    determine_move,
    get_paths,
    move_files,
    read_content,
    walk_file,
    walk_filter,
)
from logseq_analyzer.adapter.reporter import ReportWriter
from logseq_analyzer.domain.enums import BACKLINK_CRITERIA, FileType, Output
from logseq_analyzer.domain.model import LogseqFile, LogseqNode, get_data
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


def get_report(obj: Any) -> list[tuple[str, Sized]]:
    """Generate a report for the given object."""
    return [(k, getattr(obj, k)) for k in obj.__slots__]


def analyze(index: set[LogseqNode], journal_page_fmt: str) -> Iterator[tuple[str, list[tuple[str, Sized]]]]:
    """Perform core analysis on the Logseq graph."""
    analyzer = LogseqAnalyzer(index, journal_page_fmt)
    analyzer.process()
    yield "input", get_report(analyzer.inputs)
    yield "", [("dangling", analyzer.dangling)]
    yield Output.Dir.ASSET, list(analyzer.asset.items())
    yield Output.Dir.NAMESPACE, get_report(analyzer.namespace)
    yield Output.Dir.JOURNAL, [("data", analyzer.journal)]
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


@dataclass(slots=True)
class LogseqFileBuilder:
    """A builder class for creating LogseqFile instances."""

    lsconfig: LogseqConfig

    def __call__(self, path: Path, content: str) -> LogseqFile:
        """Build a LogseqFile instance from the given path and content."""
        data = {k: v for k, v in get_data(content) if v} if content else {}
        name = self.get_name(path)
        has_ns = "/" in name
        ns_part = name.split("/")
        return LogseqFile(
            path=path,
            name=name,
            filetype=self.get_filetype(path),
            has_content=bool(content),
            has_backlinks=not BACKLINK_CRITERIA.isdisjoint(data.keys()),
            is_hls=name.startswith("hls__"),
            has_ns=has_ns,
            ns_root=ns_part[0] if has_ns else "",
            ns_parent=name.rsplit("/", 1)[0] if has_ns else "",
            ns_part=ns_part,
            data=data,
        )

    def get_filetype(self, path: Path) -> str:
        """Determine the file type based on the directory structure."""
        if result := self.lsconfig.target_dirs.get(path.parent.name):
            filetype, _ = result
            return filetype
        for dirname, (_, fallback) in self.lsconfig.target_dirs.items():
            if dirname in path.parts:
                return fallback
        return FileType.OTHER

    def get_name(self, path: Path) -> str:
        """Process the filename to create a page title."""
        name = path.stem.strip(self.lsconfig.ns_sep)
        if path.parent.name == self.lsconfig.dir_journal:
            try:
                date_obj: datetime = datetime.strptime(name, self.lsconfig.jrnlfmt_file).replace(tzinfo=UTC)
                page_title: str = date_obj.strftime(self.lsconfig.jrnlfmt_page)
                if "o" in self.lsconfig.pagetitle_fmt:
                    day = str(date_obj.day)
                    day_with_ordinal = f"{day}{_get_day_ordinal(date_obj.day)}"
                    page_title = page_title.replace(day, day_with_ordinal, 1)
                return page_title.replace("'", "")
            except ValueError as e:
                logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, self.lsconfig.jrnlfmt_page, e)
                return name
        return unquote(name).replace(self.lsconfig.ns_sep, "/")


def execute_move(args: Args, paths: dict[str, Path], index: set[LogseqNode]) -> dict[str, list[Path]]:
    """Determine and execute file moves based on the provided arguments and index."""
    mover_config: dict[str, tuple[set[Path], Path, bool]] = {
        "unlinked_asset": (
            {a.path for a in index if a.filetype == FileType.ASSET and not a.backlinked},
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
    return moved


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

    prog(30, "Setup cache...")
    graph_cache = Cache(path=paths["cache"])
    cached_files = graph_cache.reset() if args.graph_cache else graph_cache.load()
    index = {LogseqNode(file=f) for f in cached_files}

    prog(40, "Process Logseq graph...")
    walk_graph = walk_filter(paths["graph"], set(lsconfig.target_dirs))
    modified_files = graph_cache.get_modified(walk_graph)
    path_content = ((p, read_content(p)) for p in modified_files)
    ls_file_builder = LogseqFileBuilder(lsconfig=lsconfig)
    for path, content in path_content:
        f = ls_file_builder(path, content)
        index.add(LogseqNode(file=f))

    prog(70, "Running core analysis on Logseq graph...")
    writer = ReportWriter(output_dir=paths["output"])
    for subdir, reports in analyze(index, lsconfig.jrnlfmt_page):
        writer.write_report(subdir, reports)

    prog(80, "Moving files...")
    moved = execute_move(args, paths, index)
    writer.write_report(Output.Dir.MOVED, [(Output.File.MOVED, moved)])

    prog(90, "Saving index to cache...")
    graph_cache.save({n.file for n in index})

    prog(100, "Logseq Analyzer completed successfully.")
