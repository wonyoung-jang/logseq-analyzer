"""Module for main application logic for the Logseq analyzer."""

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.analysis.assets import LogseqAssets
from logseq_analyzer.analysis.file import JournalFormats, LogseqFile, LogseqFileContext
from logseq_analyzer.analysis.graph import LogseqGraph
from logseq_analyzer.analysis.journals import LogseqJournals
from logseq_analyzer.analysis.namespaces import LogseqNamespaces
from logseq_analyzer.analysis.summarizers import LogseqSummarizer
from logseq_analyzer.io.cache import Cache
from logseq_analyzer.io.filemover import LogseqFileMover
from logseq_analyzer.io.filesystem import File, LogseqAnalyzerDirs
from logseq_analyzer.io.graph_config import DEFAULT_LOGSEQ_CONFIG, ConfigEdns, get_edn_from_file
from logseq_analyzer.io.report_writer import ReportWriter
from logseq_analyzer.utils.enums import FileType, Output, OutputDir, TargetDir

if TYPE_CHECKING:
    from collections.abc import Iterator

    from logseq_analyzer.analysis.index import FileIndex

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
    def report(self) -> dict[Output, list[tuple[str, object]]]:
        """Generate a report of the arguments."""
        return {
            OutputDir.META: {
                Output.ARGUMENTS: {
                    "global_config": self.global_config,
                    "graph_cache": self.graph_cache,
                    "graph_folder": self.graph_folder,
                    "move_bak": self.move_bak,
                    "move_recycle": self.move_recycle,
                    "move_unlinked_assets": self.move_unlinked_assets,
                    "report_format": self.report_format,
                    "write_graph": self.write_graph,
                },
            }
        }


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
    File(graph.path / target_dirs[TargetDir.ASSET], is_dir=True)
    File(graph.path / target_dirs[TargetDir.DRAW], is_dir=True)
    File(graph.path / target_dirs[TargetDir.JOURNAL], is_dir=True)
    File(graph.path / target_dirs[TargetDir.PAGE], is_dir=True)
    File(graph.path / target_dirs[TargetDir.WHITEBOARD], is_dir=True)
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


def _setup_journal_formats(config_edns: ConfigEdns) -> JournalFormats:
    """Set up journal formats."""
    journal_file_fmt = config_edns.get_file_name_format()
    journal_page_fmt = config_edns.get_page_title_format()
    return JournalFormats(
        file=_cljs_date_to_py(journal_file_fmt),
        page=_cljs_date_to_py(journal_page_fmt),
        page_title=journal_page_fmt,
    )


def setup_cache(args: Args, analyzer_dirs: LogseqAnalyzerDirs) -> tuple[Cache, FileIndex]:
    """Set up cache for the Logseq Analyzer."""
    cache = Cache(
        path=File(Path(Constant.CACHE_FILE), create=False).path,
        target_dirs=set(analyzer_dirs.target.values()),
        graph_dir=analyzer_dirs.graph.path,
        graph_cache=args.graph_cache,
    )
    cache.open()
    index = cache.initialize()
    return cache, index


def analyze(
    args: Args,
    index: FileIndex,
    analyzer_dirs: LogseqAnalyzerDirs,
    config_edns: ConfigEdns,
    journal_page_fmt: str,
) -> Iterator[tuple[str, dict]]:
    """Perform core analysis on the Logseq graph."""
    logseq_graph = LogseqGraph(index)
    logseq_namespaces = LogseqNamespaces(index, logseq_graph.dangling_links)
    logseq_journals = LogseqJournals(index, logseq_graph.dangling_links, journal_page_fmt)
    logseq_assets = LogseqAssets(index)
    logseq_file_mover = LogseqFileMover(
        should_move_bak=args.move_bak,
        should_move_recycle=args.move_recycle,
        should_move_unlinked_assets=args.move_unlinked_assets,
        unlinked_assets=logseq_assets.not_backlinked,
        del_assets=analyzer_dirs.del_assets.path,
        del_bak=analyzer_dirs.del_bak.path,
        del_recycle=analyzer_dirs.del_recycle.path,
        bak_dir=analyzer_dirs.bak.path,
        recycle_dir=analyzer_dirs.recycle.path,
    )
    logseq_summarizer = LogseqSummarizer(index)
    yield from args.report.items()
    yield from config_edns.report.items()
    yield from analyzer_dirs.report.items()
    yield from logseq_graph.report.items()
    yield from logseq_namespaces.report.items()
    yield from logseq_journals.report.items()
    yield from logseq_assets.report.items()
    yield from logseq_file_mover.report.items()
    yield from logseq_summarizer.report.items()
    yield from index.report.items()


def run_app(arguments: dict[str, object]) -> None:
    """Run the Logseq analyzer."""
    _init_logging()
    _prog = arguments.pop("progress_callback", lambda p, msg: logger.info("Progress: %d%% - %s", p, msg))
    _prog(10, "Starting Logseq Analyzer...")
    args = Args(**arguments)
    _prog(30, "Setting up Logseq Analyzer configurations...")
    analyzer_dirs, config_edns = _setup_logseq_paths(args)
    journal_formats = _setup_journal_formats(config_edns)
    _prog(40, "Configure Logseq Analyzer settings...")
    _context = LogseqFileContext(
        now_ts=datetime.now(tz=UTC).timestamp(),
        journal_format=journal_formats,
        ns_file_sep=config_edns.get_ns_sep(),
        journal_dir=analyzer_dirs.target[TargetDir.JOURNAL],
        graph_path=analyzer_dirs.graph.path,
        result_map={
            analyzer_dirs.target[TargetDir.ASSET]: (FileType.ASSET, FileType.SUB_ASSET),
            analyzer_dirs.target[TargetDir.DRAW]: (FileType.DRAW, FileType.SUB_DRAW),
            analyzer_dirs.target[TargetDir.JOURNAL]: (FileType.JOURNAL, FileType.SUB_JOURNAL),
            analyzer_dirs.target[TargetDir.PAGE]: (FileType.PAGE, FileType.SUB_PAGE),
            analyzer_dirs.target[TargetDir.WHITEBOARD]: (FileType.WHITEBOARD, FileType.SUB_WHITEBOARD),
        },
    )
    _prog(50, "Setup cache...")
    cache, index = setup_cache(args, analyzer_dirs)
    index.write_graph = args.write_graph
    _prog(60, "Process Logseq graph...")
    for path in cache.iter_modified_files():
        index.add(LogseqFile(path, context=_context))
    _prog(70, "Setup writer...")
    _writer = ReportWriter(ext=args.report_format, output_dir=analyzer_dirs.output.path)
    _prog(80, "Running core analysis on Logseq graph...")
    _analysis = analyze(args, index, analyzer_dirs, config_edns, journal_formats.page)
    _writer.write_reports(_analysis)
    _prog(90, "Finalizing analysis...")
    cache.close(index)
    _prog(100, "Logseq Analyzer completed successfully.")
