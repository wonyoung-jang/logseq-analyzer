"""Logseq Graph Class."""

import ast
import logging
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from logseq_analyzer.utils.enums import Core, OutputDir, TargetDir

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

logger = logging.getLogger(__name__)

type EDNValue = str | int | float | bool | None | list["EDNValue"] | set["EDNValue"] | dict[object, "EDNValue"]

TOKEN_REGEX = re.compile(r'"(?:\\.|[^"\\])*"|#\{|\{|\}|\[|\]|\(|\)|[^"\s\{\}\[\]\(\),]+')
COMMENT_REGEX = re.compile(r";.*")
NUMBER_REGEX = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


class Edn(StrEnum):
    """Enum for EDN data types."""

    FILE_NAME_FORMAT = ":journal/file-name-format"
    FILE_NAME_FORMAT_DEFAULT = "yyyy_MM_dd"
    JOURNALS_DIR = ":journals-directory"
    NS_FILE = ":file/name-format"
    PAGE_TITLE_FORMAT = ":journal/page-title-format"
    PAGE_TITLE_FORMAT_DEFAULT = "MMM do, yyyy"
    PAGES_DIR = ":pages-directory"
    PROP_PAGES = ":property-pages/enabled?"
    WHITEBOARDS_DIR = ":whiteboards-directory"


@dataclass(slots=True)
class ConfigEdns:
    """Configuration EDN files for the Logseq analyzer."""

    config: dict = field(default_factory=dict)
    default_edn: dict = field(default_factory=dict)
    user_edn: dict = field(default_factory=dict)
    global_edn: dict = field(default_factory=dict)

    def get_target_dirs(self) -> dict[str, str]:
        """Get the target directories for Logseq.

        Returns:
            dict[str, str]: A dictionary containing the target directories.

        """
        return {
            TargetDir.ASSET: TargetDir.ASSET,
            TargetDir.DRAW: TargetDir.DRAW,
            TargetDir.PAGE: str(self.config.get(Edn.PAGES_DIR, TargetDir.PAGE)),
            TargetDir.JOURNAL: str(self.config.get(Edn.JOURNALS_DIR, TargetDir.JOURNAL)),
            TargetDir.WHITEBOARD: str(self.config.get(Edn.WHITEBOARDS_DIR, TargetDir.WHITEBOARD)),
        }

    def get_page_title_format(self) -> str:
        """Get the page title format from the configuration."""
        return str(self.config.get(Edn.PAGE_TITLE_FORMAT, Edn.PAGE_TITLE_FORMAT_DEFAULT))

    def get_file_name_format(self) -> str:
        """Get the file name format from the configuration."""
        return str(self.config.get(Edn.FILE_NAME_FORMAT, Edn.FILE_NAME_FORMAT_DEFAULT))

    def get_ns_sep(self) -> str:
        """Get the namespace separator based on the configuration."""
        ns_format = self.config.get(Edn.NS_FILE, Core.NS_CONFIG_TRIPLE_LOWBAR)
        if ns_format == Core.NS_CONFIG_LEGACY:
            return Core.NS_FILE_SEP_LEGACY
        if ns_format == Core.NS_CONFIG_TRIPLE_LOWBAR:
            return Core.NS_FILE_SEP_TRIPLE_LOWBAR
        return Core.NS_FILE_SEP_TRIPLE_LOWBAR

    def get_prop_pages_enabled(self) -> bool:
        """Check if property pages are enabled in the configuration."""
        return bool(self.config.get(Edn.PROP_PAGES, True))

    @property
    def report(self) -> dict:
        """Generate a report of the configuration EDN files."""
        return {
            OutputDir.META: {
                "config_edns": {
                    "edn_default": self.default_edn,
                    "edn_user": self.user_edn,
                    "edn_global": self.global_edn,
                    "edn_config": self.config,
                }
            }
        }


@dataclass(slots=True)
class LogseqConfigEDN:
    """A simple EDN parser that converts EDN data into Python data structures."""

    tokens: list[str]
    _fn_map: dict[str, Callable[[], list | set | dict]] = field(init=False)
    _literal_map: dict[str, bool | None] = field(init=False)
    pos: int = 0

    def __post_init__(self) -> None:
        """Initialize the token map for parsing EDN structures."""
        self._fn_map = {
            "{": self.parse_map,
            "[": self.parse_vector,
            "(": self.parse_list,
            "#{": self.parse_set,
        }
        self._literal_map = {
            "true": True,
            "false": False,
            "nil": None,
        }

    def parse(self) -> EDNValue:
        """Parse the entire EDN input and return the resulting Python object."""
        value = self.parse_value()
        if self.peek() is not None:
            msg = f"Unexpected extra EDN data: {self.peek()}"
            raise ValueError(msg)
        return value

    def peek(self) -> str | None:
        """Return the next token without advancing the position."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> str | None:
        """Return the next token and advance the position."""
        tok = self.peek()
        self.pos += 1
        return tok

    def parse_value(self) -> EDNValue:
        """Parse a single EDN value."""
        tok = self.peek()
        if tok is None:
            msg = "Unexpected end of EDN input"
            raise ValueError(msg)
        if tok in self._fn_map:
            return self._fn_map[tok]()
        if tok.startswith('"'):
            return self.parse_string()
        if tok in self._literal_map:
            return self._literal_map.get(str(self.next()))
        if tok.startswith(":"):
            return self.next()
        if self.is_number(tok):
            return self.parse_number()
        return self.next()

    def parse_map(self) -> dict[EDNValue, EDNValue]:
        """Parse a map (dictionary) from EDN."""
        self.next()
        result = {}
        while True:
            if self.peek() == "}":
                self.next()
                break
            key = self.parse_value()
            if isinstance(key, dict):
                key = frozenset(key.items())
            elif isinstance(key, list):
                key = tuple(key)
            elif isinstance(key, set):
                key = frozenset(key)
            result[key] = self.parse_value()
        return result

    def parse_vector(self) -> list[EDNValue]:
        """Parse a vector (list) from EDN."""
        self.next()
        result = []
        while True:
            if self.peek() == "]":
                self.next()
                break
            result.append(self.parse_value())
        return result

    def parse_list(self) -> list[EDNValue]:
        """Parse a list from EDN."""
        self.next()
        result = []
        while True:
            if self.peek() == ")":
                self.next()
                break
            result.append(self.parse_value())
        return result

    def parse_set(self) -> set[EDNValue]:
        """Parse a set from EDN."""
        self.next()
        result = set()
        while True:
            if self.peek() == "}":
                self.next()
                break
            result.add(self.parse_value())
        return result

    def parse_string(self) -> EDNValue:
        """Parse a string from EDN."""
        return ast.literal_eval(str(self.next()))

    def is_number(self, tok: str) -> bool:
        """Check if the token is a valid number (integer or float)."""
        return NUMBER_REGEX.fullmatch(tok) is not None

    def parse_number(self) -> float | int:
        """Parse a number (integer or float) from EDN."""
        tok = self.next()
        if tok is None:
            msg = "Unexpected end of EDN input while parsing number"
            raise ValueError(msg)
        if any(c in tok for c in ".eE"):
            return float(tok)
        return int(tok)


def loads(edn_str: str) -> EDNValue:
    """Parse an EDN-formatted string and return the corresponding Python data structure.

    Args:
        edn_str (str): The EDN string to parse.

    Returns:
        EDNValue: The parsed Python data structure.

    """
    return LogseqConfigEDN(list(tokenize(edn_str))).parse()


def tokenize(edn_str: str) -> Iterator[str]:
    """Yield EDN tokens, skipping comments, whitespace, and commas.

    Comments start with ';' and run to end-of-line.
    Commas are treated as whitespace per EDN spec.

    Args:
        edn_str (str): The EDN string to tokenize.

    Yields:
        str: The next token in the EDN string.

    """
    edn = COMMENT_REGEX.sub("", edn_str)
    for match in TOKEN_REGEX.finditer(edn):
        yield match.group().strip()


def get_edn_from_file(path: Path) -> EDNValue:
    """Initialize the LogseqGraphConfig from a file.

    Args:
        path (Path): The path to the config file.

    """
    logger.debug("Initializing config from file: %s", path)
    with path.open("r", encoding="utf-8") as f:
        return loads(f.read())


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
                    [
                        "sort-by",
                        ["fn", ["h"], ["get", "h", ":block/priority", "Z"]],
                        "result",
                    ],
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
    ":graph/forcesettings": {
        ":link-dist": 180,
        ":charge-strength": -600,
        ":charge-range": 600,
    },
    ":favorites": [],
    ":srs/learning-fraction": 0.5,
    ":srs/initial-interval": 4,
    ":property-pages/enabled?": True,
    ":editor/extra-codemirror-options": {
        ":lineWrapping": False,
        ":lineNumbers": True,
        ":readOnly": False,
    },
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
