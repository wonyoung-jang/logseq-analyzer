"""
Logseq Graph Class
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Generator

from ..utils.helpers import singleton


TOKEN_REGEX = re.compile(
    r"""
    "(?:\\.|[^"\\])*"         | # strings
    \#\{                      | # set literal
    \{|\}|\[|\]|\(|\)         | # delimiters
    [^"\s\{\}\[\]\(\),]+        # atoms (numbers, symbols, keywords, etc.)
    """,
    re.VERBOSE,
)


class LogseqConfigEDN:
    """
    A simple EDN parser that converts EDN data into Python data structures.
    """

    __slots__ = ("tokens", "pos", "_tok_map")

    def __init__(self, tokens: Generator[str, Any, None]) -> None:
        """Initialize the parser with a list of tokens."""
        self.tokens = list(tokens)
        self.pos = 0
        self._tok_map = {
            "{": self.parse_map,
            "[": self.parse_vector,
            "(": self.parse_list,
            "#{": self.parse_set,
        }

    def peek(self) -> Any | None:
        """Return the next token without advancing the position."""
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> Any | None:
        """Return the next token and advance the position."""
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self) -> dict | list | set | Any | None | bool | float | int:
        """Parse the entire EDN input and return the resulting Python object."""
        value = self.parse_value()
        if self.peek() is not None:
            raise ValueError(f"Unexpected extra EDN data: {self.peek()}")
        return value

    def parse_value(self) -> dict | list | set | Any | None | bool | float | int:
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
        if self.is_number(tok):
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

    def parse_string(self) -> Any:
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

    def is_number(self, tok) -> bool:
        """Check if the token is a valid number (integer or float)."""
        return re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", tok) is not None

    def parse_number(self) -> float | int:
        """Parse a number (integer or float) from EDN."""
        tok = self.next()
        if "." in tok or "e" in tok or "E" in tok:
            return float(tok)
        return int(tok)

    def parse_keyword(self) -> Any | None:
        """Parse a keyword from EDN."""
        tok = self.next()
        return tok

    def parse_symbol(self) -> Any | None:
        """Parse a symbol from EDN."""
        tok = self.next()
        return tok


def loads(edn_str: str) -> dict | list | set | Any | None | bool | float | int:
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


DEFAULT_LOGSEQ_CONFIG_EDN = {
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


@singleton
class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    __slots__ = ("config_merged", "_config_user", "_config_global")

    def __init__(self) -> None:
        """Initialize the LogseqGraphConfig class."""
        self.config_merged: dict[str, Any] = {}
        self._config_user: dict[str, Any] = {}
        self._config_global: dict[str, Any] = {}

    def initialize_user_config_edn(self, cf_path: Path) -> None:
        """
        Extract user config.

        Args:
            cf_path (Path): The path to the config file.
        """
        with cf_path.open("r", encoding="utf-8") as user_config:
            self._config_user = loads(user_config.read())
            logging.debug("Initialized user config: %s", user_config)

    def initialize_global_config_edn(self, gcf_path: Path) -> None:
        """
        Extract global config.

        Args:
            gcf_path (Path): The path to the global config file.
        """
        with gcf_path.open("r", encoding="utf-8") as global_config:
            self._config_global = loads(global_config.read())
            logging.debug("Initialized global config: %s", global_config)

    def merge(self) -> None:
        """Merge default, user, and global config."""
        config = DEFAULT_LOGSEQ_CONFIG_EDN
        config.update(self._config_user)
        config.update(self._config_global)
        self.config_merged = config
        logging.debug("Merged config: length - %s", len(config))

    def get_user_config(self) -> dict[str, Any]:
        """Get user config."""
        return self._config_user

    def get_global_config(self) -> dict[str, Any]:
        """Get global config."""
        return self._config_global
