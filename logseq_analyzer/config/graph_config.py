"""
Logseq Graph Class
"""

import ast
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Any, Generator

from ..utils.enums import Core

logger = logging.getLogger(__name__)

__all__ = [
    "TOKEN_REGEX",
    "NUMBER_REGEX",
    "LogseqConfigEDN",
    "EDNToken",
    "loads",
    "tokenize",
    "init_config_edn_from_file",
    "get_default_logseq_config",
    "get_target_dirs",
    "get_ns_sep",
    "get_page_title_format",
    "get_file_name_format",
    "EDN",
]


type EDNToken = dict | list | set | Any | None | bool | float | int

TOKEN_REGEX: re.Pattern = re.compile(
    r"""
    "(?:\\.|[^"\\])*"         | # strings
    \#\{                      | # set literal
    \{|\}|\[|\]|\(|\)         | # delimiters
    [^"\s\{\}\[\]\(\),]+        # atoms (numbers, symbols, keywords, etc.)
    """,
    re.VERBOSE,
)
COMMENT_REGEX: re.Pattern = re.compile(r";.*")
NUMBER_REGEX: re.Pattern = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


class LogseqConfigEDN:
    """
    A simple EDN parser that converts EDN data into Python data structures.
    """

    __slots__ = ("tokens", "pos", "_tok_map")

    def __init__(self, tokens: Generator[str, Any, None]) -> None:
        """Initialize the parser with a list of tokens."""
        self.tokens: list[str] = list(tokens)
        self.pos: int = 0
        self._tok_map: dict[str, Any] = {
            "{": self.parse_map,
            "[": self.parse_vector,
            "(": self.parse_list,
            "#{": self.parse_set,
        }

    def peek(self) -> EDNToken | None:
        """Return the next token without advancing the position."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> EDNToken | None:
        """Return the next token and advance the position."""
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> EDNToken:
        """Parse the entire EDN input and return the resulting Python object."""
        value = self.parse_value()
        if self.peek() is not None:
            raise ValueError(f"Unexpected extra EDN data: {self.peek()}")
        return value

    def parse_value(self) -> EDNToken:
        """Parse a single EDN value."""
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of EDN input")
        tok_map = self._tok_map
        if tok in tok_map:
            return tok_map[tok]()
        if tok.startswith('"'):
            return self.parse_string()
        if tok in ("true", "false", "nil"):
            return self.parse_literal()
        if self.is_number(tok, NUMBER_REGEX):
            return self.parse_number()
        if tok.startswith(":"):
            return self.parse_keyword()
        return self.parse_symbol()

    def parse_map(self) -> dict:
        """Parse a map (dictionary) from EDN."""
        self.next()
        result = {}
        while True:
            tok = self.peek()
            if tok == "}":
                self.next()
                break
            key = self.parse_value()
            val = self.parse_value()
            if isinstance(key, dict):
                key = frozenset(key.items())
            elif isinstance(key, list):
                key = tuple(key)
            elif isinstance(key, set):
                key = frozenset(key)
            result[key] = val
        return result

    def parse_vector(self) -> list:
        """Parse a vector (list) from EDN."""
        self.next()
        result = []
        while True:
            tok = self.peek()
            if tok == "]":
                self.next()
                break
            result.append(self.parse_value())
        return result

    def parse_list(self) -> list:
        """Parse a list from EDN."""
        self.next()
        result = []
        while True:
            tok = self.peek()
            if tok == ")":
                self.next()
                break
            result.append(self.parse_value())
        return result

    def parse_set(self) -> set:
        """Parse a set from EDN."""
        self.next()
        result = set()
        while True:
            tok = self.peek()
            if tok == "}":
                self.next()
                break
            result.add(self.parse_value())
        return result

    def parse_string(self) -> str:
        """Parse a string from EDN."""
        tok = self.next()
        return ast.literal_eval(tok)

    def parse_literal(self) -> None | bool:
        """Parse a literal value from EDN."""
        tok = self.next()
        return {
            "true": True,
            "false": False,
            "nil": None,
        }.get(tok)

    def is_number(self, tok, number_regex: re.Pattern = NUMBER_REGEX) -> bool:
        """Check if the token is a valid number (integer or float)."""
        return number_regex.fullmatch(tok) is not None

    def parse_number(self) -> float | int:
        """Parse a number (integer or float) from EDN."""
        tok = self.next()
        if "." in tok or "e" in tok or "E" in tok:
            return float(tok)
        return int(tok)

    def parse_keyword(self) -> EDNToken | None:
        """Parse a keyword from EDN."""
        tok = self.next()
        return tok

    def parse_symbol(self) -> EDNToken | None:
        """Parse a symbol from EDN."""
        tok = self.next()
        return tok


def loads(edn_str: str) -> EDNToken:
    """
    Parse an EDN-formatted string and return the corresponding Python data structure.

    Args:
        edn_str (str): The EDN string to parse.
    Returns:
        dict | list | set | Any | None | bool | float | int: The parsed Python data structure.
    """
    parser = LogseqConfigEDN(tokenize(edn_str))
    return parser.parse()


def tokenize(edn_str: str) -> Generator[str, Any, None]:
    """
    Yield EDN tokens, skipping comments, whitespace, and commas.
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


def init_config_edn_from_file(path: Path) -> None:
    """
    Initialize the LogseqGraphConfig from a file.

    Args:
        path (Path): The path to the config file.
    """
    with path.open("r", encoding="utf-8") as f:
        edn_data = loads(f.read())
        logger.debug("Initializing config from file: %s", path)
    return edn_data


def get_default_logseq_config() -> dict[str, Any]:
    """
    Get the default Logseq configuration.

    Returns:
        dict[str, Any]: The default Logseq configuration.
    """
    return {
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


def get_target_dirs(config: dict[str, Any]) -> dict[str, str]:
    """
    Get the target directories for Logseq.

    Args:
        config (dict[str, Any]): The configuration dictionary.

    Returns:
        dict[str, str]: A dictionary containing the target directories.
    """
    return {
        "assets": "assets",
        "draws": "draws",
        "pages": config.get(EDN.PAGES_DIR.value, "pages"),
        "journals": config.get(EDN.JOURNALS_DIR.value, "journals"),
        "whiteboards": config.get(EDN.WHITEBOARDS_DIR.value, "whiteboards"),
    }


def get_ns_sep(config: dict[str, Any]) -> str:
    """Get the namespace separator based on the configuration."""
    ns_format = config.get(EDN.NS_FILE.value, Core.NS_CONFIG_TRIPLE_LOWBAR.value)
    return {
        Core.NS_CONFIG_LEGACY.value: Core.NS_FILE_SEP_LEGACY.value,
        Core.NS_CONFIG_TRIPLE_LOWBAR.value: Core.NS_FILE_SEP_TRIPLE_LOWBAR.value,
    }.get(ns_format, Core.NS_FILE_SEP_TRIPLE_LOWBAR.value)


def get_page_title_format(config: dict[str, Any]) -> str:
    """Get the page title format from the configuration."""
    return config.get(EDN.PAGE_TITLE_FORMAT.value, "MMM do, yyyy")


def get_file_name_format(config: dict[str, Any]) -> str:
    """Get the file name format from the configuration."""
    return config.get(EDN.FILE_NAME_FORMAT.value, "yyyy_MM_dd")


def get_prop_pages_enabled(config: dict[str, Any]) -> bool:
    """Check if property pages are enabled in the configuration."""
    return config.get(EDN.PROP_PAGES.value, True)


class EDN(Enum):
    """
    Enum for EDN data types.
    """

    FILE_NAME_FORMAT = ":journal/file-name-format"
    JOURNALS_DIR = ":journals-directory"
    NS_FILE = ":file/name-format"
    PAGE_TITLE_FORMAT = ":journal/page-title-format"
    PAGES_DIR = ":pages-directory"
    PROP_PAGES = ":property-pages/enabled?"
    WHITEBOARDS_DIR = ":whiteboards-directory"
