"""Module for main application logic for the Logseq analyzer."""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.adapter.ednconfig import LogseqConfig, config_from_path
from logseq_analyzer.adapter.filesystem import (
    OutputDirHandler,
    Paths,
    determine_move,
    get_paths,
    move_files,
    read_content,
    walk_file,
    walk_filter,
    write_report,
)
from logseq_analyzer.domain.enums import CriteriaGroup, FileType
from logseq_analyzer.domain.model import LogseqNode, extract_data_from_content
from logseq_analyzer.service.analysis import LogseqAnalyzer

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sized
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


def gen_report_from_data(data: Sized, level: int = 0) -> Iterator[str]:
    """Recursively format data into a string representation for reporting."""
    if level == 0:
        yield f"COUNT: {len(data)}\n"
    indent = "\t" * level
    if isinstance(data, dict):
        for key, vals in data.items():
            if level == 0:
                yield "-" * 180 + "\n"
                yield f"KEY: {key}\n"
                yield from write_toplevel(vals)
            elif isinstance(vals, (dict, list, set, tuple)):
                yield f"{indent}{key}:\n"
                yield from gen_report_from_data(vals, level + 1)
            else:
                yield f"{indent}{key:<60}: {vals}\n"
    elif isinstance(data, (list, set, tuple)):
        for i, item in enumerate(data, 1):
            if isinstance(item, (dict, list, set, tuple)):
                yield f"{indent}{i}:\n"
                yield from gen_report_from_data(item, level + 1)
            else:
                yield f"{indent}{i}\t|\t{item}\n"
    else:
        yield f"{indent}{data}\n"


def write_toplevel(vals: object) -> Iterator[str]:
    """Format top-level values with special handling for dictionaries."""
    if isinstance(vals, dict):
        for k, v in vals.items():
            if isinstance(v, (dict, list, set, tuple)):
                yield f"\t{k:<60}:\n"
                yield from gen_report_from_data(v, level=2)
            else:
                yield f"\t{k:<60}: {v}\n"
    elif isinstance(vals, (list, set, tuple)):
        yield f"\tVALUES ({len(vals)}):\n"
        yield from (f"\t{i}\t|\t{v}\n" for i, v in enumerate(vals, 1))
    else:
        yield f"VAL: {vals}\n"


def _data(outdir: Path, obj: Any) -> Iterator[tuple[Path, Iterator[str]]]:
    """Generate a report for the given object."""
    for k in obj.__slots__:
        yield outdir / f"{k}.txt", gen_report_from_data(getattr(obj, k))


def analyze(analyzer: LogseqAnalyzer, outdir_handler: OutputDirHandler) -> Iterator[tuple[Path, Iterator[str]]]:
    """Perform core analysis on the Logseq graph."""
    outdir = outdir_handler.make_subdir("")
    inputdir = outdir_handler.make_subdir("_input")
    prewritedir = outdir_handler.make_subdir("_prewrite")
    postwritedir = outdir_handler.make_subdir("_postwrite")
    namespacedir = outdir_handler.make_subdir("namespace")
    summarydir = outdir_handler.make_subdir("summary")
    yield from _data(inputdir, analyzer.inputs)
    yield from _data(prewritedir, analyzer.prewrite)
    yield from _data(postwritedir, analyzer.postwrite)
    yield from _data(namespacedir, analyzer.namespace)
    yield from _data(summarydir, analyzer.summarizer)
    yield outdir / "dangling.txt", gen_report_from_data(analyzer.dangling)
    yield outdir / "journal.txt", gen_report_from_data(analyzer.journal)
    yield outdir / "asset.txt", gen_report_from_data(analyzer.asset)
    yield outdir / "all_files.txt", gen_report_from_data(analyzer.index)
    yield outdir / "all_graph_data.txt", gen_report_from_data({(f.name, f.filetype): f.data for f in analyzer.index})


def _get_day_ordinal(d: int) -> str:
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    if 11 <= d <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")


DAY_RANGE = range(1, 32)
DAY_ORDINAL_MAP = dict(zip(DAY_RANGE, (f"{d}{_get_day_ordinal(d)}" for d in DAY_RANGE), strict=True))


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
            return self.get_journal_name(name)
        return unquote(name).replace(self.lsconfig.ns_sep, "/")

    def get_journal_name(self, name: str) -> str:
        """Convert a journal page title back to a filename."""
        try:
            date_obj: datetime = datetime.strptime(name, self.lsconfig.jrnlfmt_file).replace(tzinfo=UTC)
            page_title: str = date_obj.strftime(self.lsconfig.jrnlfmt_page)
            if "o" in self.lsconfig.pagetitle_fmt:
                d = date_obj.day
                page_title = page_title.replace(str(d), DAY_ORDINAL_MAP[d], 1)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, self.lsconfig.jrnlfmt_page, e)
            return name


def execute_move(args: Args, paths: Paths, index: set[LogseqNode]) -> dict[str, list[Path]]:
    """Determine and execute file moves based on the provided arguments and index."""
    mover_config: tuple[tuple[str, Iterable[Path], Path, bool], ...] = (
        (
            "unlinked_asset",
            (a.path for a in index if a.filetype == FileType.ASSET and not a.backlinked),
            paths.del_assets,
            args.move_unlinked_assets,
        ),
        ("bak", walk_file(paths.bak), paths.del_bak, args.move_bak),
        ("recycle", walk_file(paths.recycle), paths.del_recycle, args.move_recycle),
    )
    moved = {}
    for k, files, dest, should_move in mover_config:
        if should_move:
            key = k
            values = list(move_files(determine_move(files, dest)))
        else:
            key = f"{k} (simulated)"
            values = [f.name for f in files]
        moved[key] = values
    return moved


def summarize(cache: Cache, outdir_handler: OutputDirHandler) -> Iterator[tuple[Path, Iterator[str]]]:
    """Summarize the graph cache for debugging purposes."""
    outdir = outdir_handler.make_subdir("summary/file")
    names = ("has_content", "has_backlinks", "backlinked", "backlinked_ns_only")
    for name in names:
        data = cache.get("name", name, True)
        yield outdir / f"{name}.txt", gen_report_from_data(data)


def run_app(args: Args, progress_callback: Callable[[int, str], None] | None = None) -> None:
    """Run the Logseq analyzer."""
    init_logging()
    prog = progress_callback or (lambda p, msg: logger.debug("Progress: %d%% - %s", p, msg))
    prog(0, "Start...")

    prog(10, "Setup...")
    paths = get_paths(args.graph_folder, args.global_config)
    lsconfig = LogseqConfig.from_config(config_from_path(paths.config_user, paths.config_global))
    cache = Cache(path=paths.cache)
    index: set[LogseqNode] = cache.reset() if args.graph_cache else cache.load()

    prog(20, "Process...")
    walk_graph = walk_filter(paths.graph, lsconfig.target_dirs)
    modified_files = cache.get_modified_path(walk_graph)
    builder = LogseqFileBuilder(lsconfig=lsconfig)
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(builder, path): path for path in modified_files}
        for future in as_completed(futures):
            index.add(future.result())

    prog(60, "Analyzing...")
    analyzer = LogseqAnalyzer(index, lsconfig.jrnlfmt_page)
    analyzer()

    prog(70, "Saving...")
    cache.save(index)

    prog(80, "Writing...")
    outdir_handler = OutputDirHandler(rootdir=paths.output)
    for path, data in analyze(analyzer, outdir_handler):
        write_report(path, data)
    for path, data in summarize(cache, outdir_handler):
        write_report(path, data)

    prog(90, "Moving...")
    moved = execute_move(args, paths, index)
    outdir = outdir_handler.make_subdir("")
    write_report(outdir / "moved.txt", gen_report_from_data(moved))

    prog(100, "Analyzer completed successfully.")
