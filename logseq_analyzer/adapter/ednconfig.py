"""Logseq Graph Class."""

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.adapter.filesystem import read_content
from logseq_analyzer.domain.enums import FileType, TargetDir
from logseq_analyzer.domain.patterns import EDNPattern, cljs_date_to_py

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from pathlib import Path

logger = logging.getLogger(__name__)

LITERAL_MAP = {"true": True, "false": False, "nil": None}


@dataclass(slots=True)
class LogseqConfig:
    """Class to represent the Logseq configuration."""

    dir_page: str
    dir_journal: str
    dir_whiteboard: str
    pagetitle_fmt: str
    filename_fmt: str
    jrnlfmt_page: str
    jrnlfmt_file: str
    ns_sep: str
    target_dirs: dict[str, tuple[str, str, str]]

    @classmethod
    def from_config(cls, config: dict) -> LogseqConfig:
        """Create a LogseqConfig instance from a configuration dictionary."""
        dir_page = config.get(":pages-directory", TargetDir.PAGE)
        dir_journal = config.get(":journals-directory", TargetDir.JOURNAL)
        dir_whiteboard = config.get(":whiteboards-directory", TargetDir.WHITEBOARD)
        pagetitle_fmt = config.get(":journal/page-title-format", "MMM do, yyyy")
        filename_fmt = config.get(":journal/file-name-format", "yyyy_MM_dd")
        ns_sep = "%2F" if config.get(":file/name-format", ":triple-lowbar") == ":legacy" else "___"
        return cls(
            dir_page=dir_page,
            dir_journal=dir_journal,
            dir_whiteboard=dir_whiteboard,
            pagetitle_fmt=pagetitle_fmt,
            filename_fmt=filename_fmt,
            jrnlfmt_page=cljs_date_to_py(pagetitle_fmt),
            jrnlfmt_file=cljs_date_to_py(filename_fmt),
            ns_sep=ns_sep,
            target_dirs={
                TargetDir.ASSET: (TargetDir.ASSET, FileType.ASSET, FileType.SUB_ASSET),
                TargetDir.DRAW: (TargetDir.DRAW, FileType.DRAW, FileType.SUB_DRAW),
                TargetDir.PAGE: (dir_page, FileType.PAGE, FileType.SUB_PAGE),
                TargetDir.JOURNAL: (dir_journal, FileType.JOURNAL, FileType.SUB_JOURNAL),
                TargetDir.WHITEBOARD: (dir_whiteboard, FileType.WHITEBOARD, FileType.SUB_WHITEBOARD),
            },
        )


def config_from_path(config_user: Path, config_global: Path | None) -> dict:
    """Create a ConfigEdns instance from user and global EDN files."""
    logger.debug("Loading user config from file: %s", config_user)
    user_edn_parsed = parse_edn(read_content(config_user))
    user_edn = user_edn_parsed if isinstance(user_edn_parsed, dict) else {}
    global_edn = {}
    if config_global:
        logger.debug("Loading global config from file: %s", config_global)
        global_edn_parsed = parse_edn(read_content(config_global))
        if isinstance(global_edn_parsed, dict):
            global_edn = global_edn_parsed
    return DEFAULT_LOGSEQ_CONFIG | user_edn | global_edn


@dataclass(slots=True)
class EDNParser:
    """A simple EDN parser that converts EDN data into Python data structures."""

    tokens: Sequence[str]
    pos: int = 0
    _fn_map: dict[str, Callable[[], list | set | dict]] = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the token map for parsing EDN structures."""
        self._fn_map = {
            "{": self.parse_map,
            "[": lambda: self.parse_sequence(closing="]"),
            "(": lambda: self.parse_sequence(closing=")"),
            "#{": self.parse_set,
        }

    def parse(self) -> Any:
        """Parse the entire EDN input and return the resulting Python object."""
        value = self.parse_value()
        if self._peek() is not None:
            msg = f"Unexpected extra EDN data: {self._peek()}"
            raise ValueError(msg)
        return value

    def _peek(self) -> str | None:
        """Return the next token without advancing the position."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> str:
        """Return the next token and advance the position."""
        tok = self._peek()
        if tok is None:
            msg = "Unexpected end of EDN input"
            raise ValueError(msg)
        self.pos += 1
        return tok

    def parse_value(self) -> Any:
        """Parse a single EDN value."""
        tok = self._peek()
        if tok is None:
            msg = "Unexpected end of EDN input"
            raise ValueError(msg)
        if tok in self._fn_map:
            return self._fn_map[tok]()
        if tok.startswith('"'):
            return self.parse_string()
        if tok.startswith(":"):
            return self._next()
        if tok in LITERAL_MAP:
            return LITERAL_MAP.get(self._next())
        if EDNPattern.NUMBER.fullmatch(tok) is not None:
            return self.parse_number()
        return self._next()

    def parse_map(self) -> dict[Any, Any]:
        """Parse a map (dictionary) from EDN."""
        self._next()
        result = {}
        while self._peek() != "}":
            key = self.parse_value()
            key_hashed = self.make_hashable(key)
            result[key_hashed] = self.parse_value()
        self._next()
        return result

    def make_hashable(self, val: Any) -> Any:
        """Convert an EDN value to a hashable Python object."""
        if isinstance(val, dict):
            return frozenset((k, self.make_hashable(v)) for k, v in val.items())
        if isinstance(val, list):
            return tuple(val)
        if isinstance(val, set):
            return frozenset(val)
        return val

    def parse_sequence(self, closing: str) -> list[Any]:
        """Parse a vector (list) from EDN."""
        self._next()
        result = []
        while self._peek() != closing:
            result.append(self.parse_value())
        self._next()
        return result

    def parse_set(self) -> set[Any]:
        """Parse a set from EDN."""
        self._next()
        result = set()
        while self._peek() != "}":
            result.add(self.parse_value())
        self._next()
        return result

    def parse_string(self) -> Any:
        """Parse a string from EDN."""
        return json.loads(self._next())

    def parse_number(self) -> int | float:
        """Parse a number (integer or float) from EDN."""
        tok = self._next()
        if "." in tok or "e" in tok.lower():
            return float(tok)
        return int(tok)


def tokenize(edn_str: str) -> Iterator[str]:
    """Yield EDN tokens, skipping comments, whitespace, and commas."""
    edn = EDNPattern.COMMENT.sub("", edn_str)
    for match in EDNPattern.TOKEN.finditer(edn):
        yield match.group().strip()


def parse_edn(edn_str: str) -> Any:
    """Parse an EDN-formatted string and return the corresponding Python data structure."""
    tokens = tuple(tokenize(edn_str))
    return EDNParser(tokens).parse()


DEFAULT_LOGSEQ_CONFIG = {
    ":meta/version": 1,
    ":preferred-format": "Markdown",
    ":preferred-workflow": ":now",
    ":hidden": [],
    ":default-templates": {":journals": ""},
    ":journal/page-title-format": "MMM do, yyyy",
    ":journal/file-name-format": "yyyy_MM_dd",
    ":ui/enable-tooltip?": True,
    ":ui/show-brackets?": True,
    ":ui/show-full-blocks?": False,
    ":ui/auto-expand-block-refs?": True,
    ":feature/enable-block-timestamps?": False,
    ":feature/enable-search-remove-accents?": True,
    ":feature/enable-journals?": True,
    ":feature/enable-flashcards?": True,
    ":feature/enable-whiteboards?": True,
    ":feature/disable-scheduled-and-deadline-query?": False,
    ":scheduled/future-days": 7,
    ":start-of-week": 6,
    ":export/bullet-indentation": ":tab",
    ":publishing/all-pages-public?": False,
    ":pages-directory": "pages",
    ":journals-directory": "journals",
    ":whiteboards-directory": "whiteboards",
    ":shortcuts": {},
    ":shortcut/doc-mode-enter-for-new-block?": False,
    ":block/content-max-length": 10000,
    ":ui/show-command-doc?": True,
    ":ui/show-empty-bullets?": False,
    ":query/views": {":pprint": ["fn", ["r"], [":pre.code", ["pprint", "r"]]]},
    ":query/result-transforms": {
        ":sort-by-priority": [
            "fn",
            ["result"],
            ["sort-by", ["fn", ["h"], ["get", "h", ":block/priority", "Z"]], "result"],
        ]
    },
    ":default-queries": {
        ":journals": [
            {
                ":title": "🔨 NOW",
                ":query": [
                    ":find",
                    ["pull", "?h", ["*"]],
                    ":in",
                    "$",
                    "?start",
                    "?today",
                    ":where",
                    ["?h", ":block/marker", "?marker"],
                    [["contains?", {"NOW", "DOING"}, "?marker"]],
                    ["?h", ":block/page", "?p"],
                    ["?p", ":block/journal?", True],
                    ["?p", ":block/journal-day", "?d"],
                    [[">=", "?d", "?start"]],
                    [["<=", "?d", "?today"]],
                ],
                ":inputs": [":14d", ":today"],
                ":result-transform": [
                    "fn",
                    ["result"],
                    ["sort-by", ["fn", ["h"], ["get", "h", ":block/priority", "Z"]], "result"],
                ],
                ":group-by-page?": False,
                ":collapsed?": False,
            },
            {
                ":title": "📅 NEXT",
                ":query": [
                    ":find",
                    ["pull", "?h", ["*"]],
                    ":in",
                    "$",
                    "?start",
                    "?next",
                    ":where",
                    ["?h", ":block/marker", "?marker"],
                    [["contains?", {"NOW", "LATER", "TODO"}, "?marker"]],
                    ["?h", ":block/page", "?p"],
                    ["?p", ":block/journal?", True],
                    ["?p", ":block/journal-day", "?d"],
                    [[">", "?d", "?start"]],
                    [["<", "?d", "?next"]],
                ],
                ":inputs": [":today", ":7d-after"],
                ":group-by-page?": False,
                ":collapsed?": False,
            },
        ]
    },
    ":commands": [],
    ":outliner/block-title-collapse-enabled?": False,
    ":macros": {},
    ":ref/default-open-blocks-level": 2,
    ":ref/linked-references-collapsed-threshold": 100,
    ":graph/settings": {
        ":orphan-pages?": True,
        ":builtin-pages?": False,
        ":excluded-pages?": False,
        ":journal?": False,
    },
    ":graph/forcesettings": {":link-dist": 180, ":charge-strength": -600, ":charge-range": 600},
    ":favorites": [],
    ":srs/learning-fraction": 0.5,
    ":srs/initial-interval": 4,
    ":property-pages/enabled?": True,
    ":editor/extra-codemirror-options": {":lineWrapping": False, ":lineNumbers": True, ":readOnly": False},
    ":editor/logical-outdenting?": False,
    ":editor/preferred-pasting-file?": False,
    ":dwim/settings": {
        ":admonition&src?": True,
        ":markup?": False,
        ":block-ref?": True,
        ":page-ref?": True,
        ":properties?": True,
        ":list?": False,
    },
    ":file/name-format": ":triple-lowbar",
}
