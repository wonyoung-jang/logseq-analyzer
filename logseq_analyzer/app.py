"""Module for main application logic for the Logseq analyzer."""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
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
from logseq_analyzer.domain.enums import CriteriaGroup, FileType, Output
from logseq_analyzer.domain.model import LogseqNode, extract_data_from_content
from logseq_analyzer.service.analysis import LogseqAnalyzer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sized
    from pathlib import Path


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


def init_logging() -> None:
    """Initialize logging for the application."""
    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
        filemode="w",
        filename="logseq_analyzer.log",
        force=True,
        format="%(asctime)s - %(levelname)s:%(name)s - %(message)s",
        level=logging.DEBUG,
    )


def analyze(analyzer: LogseqAnalyzer) -> Iterator[tuple[str, list[tuple[str, Sized]]]]:
    """Perform core analysis on the Logseq graph."""

    def get_report(obj: Any) -> list[tuple[str, Sized]]:
        """Generate a report for the given object."""
        return [(k, getattr(obj, k)) for k in obj.__slots__]

    yield "_input", get_report(analyzer.inputs)
    yield "_prewrite", get_report(analyzer.prewrite)
    yield "_postwrite", get_report(analyzer.postwrite)
    yield "", [("dangling", analyzer.dangling)]
    yield "", list(analyzer.asset.items())
    yield "", [("journal", analyzer.journal)]
    yield Output.Dir.NAMESPACE, get_report(analyzer.namespace)
    report = []
    report.append(("_all_files", analyzer.index))
    report.append(("_all_graph_data", {(f.name, f.filetype): f.data for f in analyzer.index}))
    yield "", report


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

    def __call__(self, path: Path) -> LogseqNode:
        """Build a LogseqFile instance from the given path and content."""
        content = read_content(path)
        data = {k: v for k, v in extract_data_from_content(content) if v} if content else {}
        name = self.get_name(path)
        has_ns = "/" in name
        return LogseqNode(
            path=path,
            name=name,
            filetype=self.get_filetype(path),
            ns_root=name.split("/", 1)[0] if has_ns else "",
            ns_parent=name.rsplit("/", 1)[0] if has_ns else "",
            has_content=bool(content),
            has_backlinks=not CriteriaGroup.BACKLINK.value.isdisjoint(data.keys()),
            data=data,
        )

    def get_filetype(self, path: Path) -> str:
        """Determine the file type based on the directory structure."""
        for p in path.parents:
            if filetype := self.lsconfig.target_dirs.get(p.name):
                return filetype
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


def summarize(graph_cache: Cache) -> Iterator[tuple[str, list[tuple[str, Sized]], str]]:
    """Summarize the graph cache for debugging purposes."""
    has_content = graph_cache.get("name", "has_content", True)
    has_backlinks = graph_cache.get("name", "has_backlinks", True)
    is_backlinked = graph_cache.get("name", "backlinked", True)
    is_backlinked_ns_only = graph_cache.get("name", "backlinked_ns_only", True)
    yield Output.Dir.SUMMARY, [(Output.File.SUMMARY_HAS_CONTENT, has_content)], "file"
    yield Output.Dir.SUMMARY, [(Output.File.SUMMARY_HAS_BACKLINK, has_backlinks)], "file"
    yield Output.Dir.SUMMARY, [(Output.File.SUMMARY_BACKLINKED, is_backlinked)], "file"
    yield Output.Dir.SUMMARY, [(Output.File.SUMMARY_BACKLINKED_NS_ONLY, is_backlinked_ns_only)], "file"


def run_app(arguments: dict, progress_callback: Callable[[int, str], None] | None = None) -> None:
    """Run the Logseq analyzer."""
    init_logging()
    prog = progress_callback or (lambda p, msg: logger.debug("Progress: %d%% - %s", p, msg))
    args = Args(**arguments)
    prog(0, "Analyzer started...")

    prog(20, "Setup...")
    paths = get_paths(args.graph_folder, args.global_config)
    lsconfig = LogseqConfig.from_config(config_from_path(paths["config_user"], paths.get("config_global")))
    graph_cache = Cache(path=paths["cache"])
    index: set[LogseqNode] = graph_cache.reset() if args.graph_cache else graph_cache.load()

    prog(40, "Process graph...")
    walk_graph = walk_filter(paths["graph"], set(lsconfig.target_dirs))
    modified_files = graph_cache.get_modified_path(walk_graph)
    builder = LogseqFileBuilder(lsconfig=lsconfig)
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(builder, path): path for path in modified_files}
        for future in as_completed(futures):
            index.add(future.result())

    prog(70, "Analyzing...")
    analyzer = LogseqAnalyzer(index, lsconfig.jrnlfmt_page)
    analyzer()
    graph_cache.save(index)

    prog(80, "Writing...")
    writer = ReportWriter(root_dirname=paths["output"])
    for dirname, data in analyze(analyzer):
        writer.generate(dirname, data)
    for dirname, data, subdir in summarize(graph_cache):
        writer.generate(dirname, data, subdir=subdir)

    prog(90, "Moving...")
    moved = execute_move(args, paths, index)
    writer.generate("", [(Output.File.MOVED, moved)])

    prog(100, "Analyzer completed successfully.")
