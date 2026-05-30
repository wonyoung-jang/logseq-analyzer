"""Logseq Graph Class."""

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.adapter.filesystem import DATADIR, File, read_content
from logseq_analyzer.domain.enums import FileType
from logseq_analyzer.domain.patterns import EDNPattern, cljs_date_to_py

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from pathlib import Path

logger = logging.getLogger(__name__)

LITERAL_MAP = {"true": True, "false": False, "nil": None}


def _config_from_path(path: Path | None) -> dict:
    """Load and parse the EDN configuration file from the given path."""
    if not path:
        return {}
    logger.debug("Loading config from file: %s", path)
    parsed_edn = parse_edn(read_content(path))
    return parsed_edn if isinstance(parsed_edn, dict) else {}


def config_from_path(config_user: Path, config_global: Path | None) -> dict:
    """Create a ConfigEdns instance from user and global EDN files."""
    default_edn = _config_from_path(DATADIR / File.App.DEFAULT_EDN)
    user_edn = _config_from_path(config_user)
    global_edn = _config_from_path(config_global)
    return default_edn | user_edn | global_edn


def tokenize(edn_str: str) -> Iterator[str]:
    """Yield EDN tokens, skipping comments, whitespace, and commas."""
    edn = EDNPattern.COMMENT.sub("", edn_str)
    for match in EDNPattern.TOKEN.finditer(edn):
        yield match.group().strip()


def parse_edn(edn_str: str) -> Any:
    """Parse an EDN-formatted string and return the corresponding Python data structure."""
    tokens = tuple(tokenize(edn_str))
    return EDNParser(tokens).parse()


@dataclass(slots=True)
class LogseqConfig:
    """Class to represent the Logseq configuration."""

    pagetitle_fmt: str
    filename_fmt: str
    jrnlfmt_page: str
    jrnlfmt_file: str
    filename_ns_sep: str
    target_dirs: dict[str, str]

    @classmethod
    def from_config(cls, config: dict) -> LogseqConfig:
        """Create a LogseqConfig instance from a configuration dictionary."""
        dir_asset = config.get(":assets-directory", "assets")
        dir_draw = config.get(":draws-directory", "draws")
        dir_page = config.get(":pages-directory", "pages")
        dir_journal = config.get(":journals-directory", "journals")
        dir_whiteboard = config.get(":whiteboards-directory", "whiteboards")
        pagetitle_fmt = config.get(":journal/page-title-format", "MMM do, yyyy")
        filename_fmt = config.get(":journal/file-name-format", "yyyy_MM_dd")
        filename_ns_sep = "%2F" if config.get(":file/name-format", ":triple-lowbar") == ":legacy" else "___"
        return cls(
            pagetitle_fmt=pagetitle_fmt,
            filename_fmt=filename_fmt,
            jrnlfmt_page=cljs_date_to_py(pagetitle_fmt),
            jrnlfmt_file=cljs_date_to_py(filename_fmt),
            filename_ns_sep=filename_ns_sep,
            target_dirs={
                dir_asset: FileType.ASSET,
                dir_draw: FileType.DRAW,
                dir_page: FileType.PAGE,
                dir_journal: FileType.JOURNAL,
                dir_whiteboard: FileType.WHITEBOARD,
            },
        )


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
