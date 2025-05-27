"""
Logseq Graph Class
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Generator

from ..utils.enums import Output
from ..utils.helpers import singleton

__all__ = [
    "TOKEN_REGEX",
    "NUMBER_REGEX",
    "DEFAULT_LOGSEQ_CONFIG_EDN",
    "LogseqConfigEDN",
    "LogseqGraphConfig",
    "EDNToken",
    "loads",
    "tokenize",
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

NUMBER_REGEX: re.Pattern = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


DEFAULT_LOGSEQ_CONFIG_EDN: dict[str, Any] = {
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
    tokens = tokenize(edn_str)
    parser = LogseqConfigEDN(tokens)
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
    edn_str = re.sub(r";.*", "", edn_str)
    for match in TOKEN_REGEX.finditer(edn_str):
        tok = match.group().strip()
        yield tok


def init_config_edn_from_file(path: Path) -> None:
    """
    Initialize the LogseqGraphConfig from a file.

    Args:
        path (Path): The path to the config file.
    """
    with path.open("r", encoding="utf-8") as file:
        edn_data = file.read()
        logging.debug("Initializing config from file: %s", path)
    return loads(edn_data)


@singleton
class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    __slots__ = ("config", "_user_edn", "_global_edn")

    def __init__(self) -> None:
        """Initialize the LogseqGraphConfig class."""
        self.config: dict[str, Any] = {}

    @property
    def user_edn(self) -> dict[str, Any]:
        """Return the user configuration."""
        return self._user_edn

    @user_edn.setter
    def user_edn(self, value: Any) -> None:
        """Set the user configuration."""
        if not isinstance(value, dict):
            raise ValueError("User config must be a dictionary.")
        self._user_edn = value

    @property
    def global_edn(self) -> dict[str, Any]:
        """Return the global configuration."""
        return self._global_edn

    @global_edn.setter
    def global_edn(self, value: Any) -> None:
        """Set the global configuration."""
        if not isinstance(value, dict):
            raise ValueError("Global config must be a dictionary.")
        self._global_edn = value

    def merge(self) -> None:
        """Merge default, user, and global config."""
        config = DEFAULT_LOGSEQ_CONFIG_EDN
        config.update(self.user_edn)
        config.update(self.global_edn)
        self.config = config
        logging.debug("Merged config: length - %s", len(config))

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the merged configuration."""
        return {
            Output.CONFIG_MERGED.value: self.config,
            Output.CONFIG_USER.value: self.user_edn,
            Output.CONFIG_GLOBAL.value: self.global_edn,
        }
