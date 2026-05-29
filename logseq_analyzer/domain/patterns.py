"""Hierarchical patterns for elements."""

import re
from typing import TYPE_CHECKING

from logseq_analyzer.domain.enums import Crit

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

DT_TOKEN_MAP: dict[str, str] = {
    "a": "%p",
    "A": "%p",
    "d": "%#d",
    "D": "%j",
    "dd": "%d",
    "E": "%a",
    "e": "%u",
    "EE": "%a",
    "EEE": "%a",
    "EEEE": "%A",
    "H": "%H",
    "h": "%I",
    "HH": "%H",
    "hh": "%I",
    "m": "%#M",
    "M": "%#m",
    "mm": "%M",
    "MM": "%m",
    "MMM": "%b",
    "MMMM": "%B",
    "s": "%#S",
    "ss": "%S",
    "SSS": "%f",
    "xx": "%y",
    "xxxx": "%Y",
    "yy": "%y",
    "yyyy": "%Y",
    "Z": "%z",
    "ZZ": "%z",
}
_SORTED_DT_TOKEN = list(DT_TOKEN_MAP.keys())
_SORTED_DT_TOKEN.sort(key=len, reverse=True)
DT_TOKEN_PATTERN: re.Pattern = re.compile("|".join(_SORTED_DT_TOKEN))
DT_ORDINAL_PATTERN = re.compile(r"(?<=\d)(st|nd|rd|th)\b")


def cljs_date_to_py(cljs_format: str) -> str:
    """Convert a Clojure-style date format to a Python-style date format."""

    def _repl(match: re.Match) -> str:
        """Replace a date token with its corresponding Python format."""
        token = match.group(0)
        return DT_TOKEN_MAP.get(token, token)

    return DT_TOKEN_PATTERN.sub(_repl, cljs_format.replace("o", ""))


class EDNPattern:
    """Class to hold compiled regex patterns for EDN content."""

    TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|#\{|\{|\}|\[|\]|\(|\)|[^"\s\{\}\[\]\(\),]+')
    COMMENT = re.compile(r";.*")
    NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_URL = (
    r"(?:(?:https?|ftp)://)"
    r"(?:\S+(?::\S*)?@)?"
    r"(?:\d{1,3}(?:\.\d{1,3}){3}|\[[0-9A-F:]+\]|(?:[A-Z0-9-]+\.)+[A-Z]{2,})"
    r"(?::\d{2,5})?(?:/[^\s]*)?"
    r'(?:\s+["\'][^)]*["\'])?'
)


class ContentPatterns:
    """Class to hold compiled regex patterns for Logseq content."""

    ANY_LINK = re.compile(rf"\b(?:{_URL})\b", re.IGNORECASE)
    ASSET = re.compile(r"assets/(?:.*/)?([^\s/]+\.\w{2,5})(?=\W|$)", re.IGNORECASE)
    BLOCKQUOTE = re.compile(r"(?!^[^\S\n])(- >.*)", re.MULTILINE | re.IGNORECASE)
    BULLET = re.compile(r"^\s*-\s*", re.MULTILINE | re.IGNORECASE)
    DRAW = re.compile(r"(?<!#)\[\[draws/(.+?)\.excalidraw\]\]", re.IGNORECASE)
    DYNAMIC_VARIABLE = re.compile(r"<%\s*.*?\s*%>", re.IGNORECASE)
    FLASHCARD = re.compile(r"(?!^[^\S\n])(- [^\n]*#card|\[\[card\]\].*)", re.MULTILINE | re.IGNORECASE)
    INLINE_CODE = re.compile(r"`[^`\n]+`", re.IGNORECASE)
    PAGE_REFERENCE = re.compile(r"(?<!#)\[\[(.+?)\]\]", re.IGNORECASE)
    PROPERTY = re.compile(r"^(?!\s*-\s)\s*([A-Za-z0-9_-]+)(?=::)", re.MULTILINE | re.IGNORECASE)
    PROPERTY_VALUE = re.compile(r"^(?!\s*-\s)\s*([A-Za-z0-9_-]+)::(.*)$", re.MULTILINE | re.IGNORECASE)
    TAG = re.compile(r"#(?!\[\[)([^\]#\s]+)", re.IGNORECASE)
    TAGGED_BACKLINK = re.compile(r"#\[\[([^\]#]+?)\]\]", re.IGNORECASE)


def _advcmd() -> re.Pattern:
    return re.compile(r"#\+BEGIN_.*?#\+END_.*?(?:\n|$)", re.DOTALL | re.IGNORECASE)


def _advcmd_child(key: str, variant: str = "") -> re.Pattern:
    _key = rf"{key}\s{variant}" if variant else key
    return re.compile(rf"#\+BEGIN_{_key}", re.IGNORECASE)


def _mlcode() -> re.Pattern:
    return re.compile(r"```.*?```", re.DOTALL | re.IGNORECASE)


def _mlcode_child(key: str) -> re.Pattern:
    return re.compile(rf"```{key}", re.IGNORECASE)


def _dblcurly(key: str, suffix: str = "") -> re.Pattern:
    _key = rf"{key} " if key else ""
    return re.compile(rf"\{{\{{{_key}{suffix or r'.*?'}\}}\}}", re.IGNORECASE)


def _dblparen(key: str) -> re.Pattern:
    return re.compile(rf"(?<!\{{\{{embed )\(\({key or r'.*?'}\)\)", re.IGNORECASE)


def _emblink(key: str) -> re.Pattern:
    return re.compile(rf"\!\[.*?\]\({key or r'.*?'}\)", re.IGNORECASE)


def _extlink(key: str) -> re.Pattern:
    return re.compile(rf"(?<!\!)\[.*?\]\({key or r'.*?'}\)", re.IGNORECASE)


class IPattern:
    """Base pattern class."""

    ALL: re.Pattern
    PATTERN: Sequence[tuple[str, re.Pattern]]
    FALLBACK: str
    _GROUP_MAP: dict[str, str]
    _DISPATCHER: re.Pattern

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Build a combined dispatcher pattern for the subclass based on its PATTERN attribute."""
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "PATTERN"):
            return
        parts: list[str] = []
        group_map: dict[str, str] = {}
        for idx, (prefix, pat) in enumerate(cls.PATTERN):
            gname = f"g{idx}"
            parts.append(f"(?P<{gname}>{pat.pattern})")
            group_map[gname] = prefix
        cls._GROUP_MAP = group_map
        cls._DISPATCHER = re.compile("|".join(parts), re.DOTALL | re.IGNORECASE)

    @classmethod
    def process_hierarchy(cls, content: str) -> Iterator[tuple[str, str]]:
        """Yield (prefix, matched_value) pairs for all ALL-matches in content.

        Uses a single combined dispatcher pattern for O(1) sub-type dispatch
        per match instead of iterating every sub-pattern sequentially.
        """
        for match in cls.ALL.finditer(content):
            value = match.group(0)
            if sub := cls._DISPATCHER.search(value):
                yield cls._GROUP_MAP[sub.lastgroup], value
            else:
                yield cls.FALLBACK, value


class AdvCmdPatterns(IPattern):
    """Patterns for advanced commands in Logseq."""

    ALL = _advcmd()
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.AdvCmd.EXPORT, _advcmd_child("EXPORT")),
        (Crit.AdvCmd.EXPORT_ASCII, _advcmd_child("EXPORT", "ascii")),
        (Crit.AdvCmd.EXPORT_LATEX, _advcmd_child("EXPORT", "latex")),
        (Crit.AdvCmd.CAUTION, _advcmd_child("CAUTION")),
        (Crit.AdvCmd.CENTER, _advcmd_child("CENTER")),
        (Crit.AdvCmd.COMMENT, _advcmd_child("COMMENT")),
        (Crit.AdvCmd.EXAMPLE, _advcmd_child("EXAMPLE")),
        (Crit.AdvCmd.IMPORTANT, _advcmd_child("IMPORTANT")),
        (Crit.AdvCmd.NOTE, _advcmd_child("NOTE")),
        (Crit.AdvCmd.PINNED, _advcmd_child("PINNED")),
        (Crit.AdvCmd.QUERY, _advcmd_child("QUERY")),
        (Crit.AdvCmd.QUOTE, _advcmd_child("QUOTE")),
        (Crit.AdvCmd.TIP, _advcmd_child("TIP")),
        (Crit.AdvCmd.VERSE, _advcmd_child("VERSE")),
        (Crit.AdvCmd.WARNING, _advcmd_child("WARNING")),
    )
    FALLBACK = Crit.AdvCmd.ALL


class CodePatterns(IPattern):
    """Patterns for code blocks in Logseq."""

    ALL = _mlcode()
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.MultLineCode.CALC, _mlcode_child("calc")),
        (Crit.MultLineCode.LANGUAGE, _mlcode_child(r"\w+")),
    )
    FALLBACK = Crit.MultLineCode.ALL


class DoubleCurlyPatterns(IPattern):
    """Patterns for double curly braces in Logseq."""

    ALL = _dblcurly("")
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.DblCurly.EMBED, _dblcurly("embed")),
        (Crit.DblCurly.PAGE_EMBED, _dblcurly("embed", r"\[\[.*?\]\]")),
        (Crit.DblCurly.BLOCK_EMBED, _dblcurly("embed", rf"\(\({_UUID}\)\)")),
        (Crit.DblCurly.NAMESPACE_QUERY, _dblcurly("namespace")),
        (Crit.DblCurly.CARD, _dblcurly("cards")),
        (Crit.DblCurly.CLOZE, _dblcurly("cloze")),
        (Crit.DblCurly.SIMPLE_QUERY, _dblcurly("query")),
        (Crit.DblCurly.QUERY_FUNCTION, _dblcurly("function")),
        (Crit.DblCurly.EMBED_VIDEO_URL, _dblcurly("video")),
        (Crit.DblCurly.EMBED_TWITTER_TWEET, _dblcurly("tweet")),
        (Crit.DblCurly.YOUTUBE_TIMESTAMP, _dblcurly("youtube-timestamp")),
        (Crit.DblCurly.RENDERER, _dblcurly("renderer")),
    )
    FALLBACK = Crit.DblCurly.ALL


class DoubleParenthesesPatterns(IPattern):
    """Patterns for double parentheses in Logseq."""

    ALL = _dblparen("")
    PATTERN: Sequence[tuple[str, re.Pattern]] = ((Crit.DblParen.BLOCK_REF, _dblparen(_UUID)),)
    FALLBACK = Crit.DblParen.ALL


class EmbeddedLinkPatterns(IPattern):
    """Patterns for embedded links in Logseq."""

    ALL = _emblink("")
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.EmbLink.INTERNET, _emblink(_URL)),
        (Crit.EmbLink.ASSET, _emblink(r".*?assets/(?:.*/)?([^\s/]+\.\w{2,5})(?=\W|$)")),
    )
    FALLBACK = Crit.EmbLink.ALL


class ExternalLinkPatterns(IPattern):
    """Patterns for external links in Logseq."""

    ALL = _extlink("")
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.ExtLink.INTERNET, _extlink(_URL)),
        (Crit.ExtLink.ALIAS, _extlink(r"[\[{2}|\({2}].*?[\]{2}|\){2}].*?")),
    )
    FALLBACK = Crit.ExtLink.ALL


HIERARCHICAL_PATTERN: Sequence[type[IPattern]] = (
    AdvCmdPatterns,
    CodePatterns,
    DoubleCurlyPatterns,
    DoubleParenthesesPatterns,
    EmbeddedLinkPatterns,
    ExternalLinkPatterns,
)
MASK_PATTERN: Sequence[tuple[str, re.Pattern[str]]] = (
    (Crit.MultLineCode.ALL, CodePatterns.ALL),
    (Crit.Content.INLINE_CODE, ContentPatterns.INLINE_CODE),
    (Crit.AdvCmd.ALL, AdvCmdPatterns.ALL),
    (Crit.Content.ANY_LINK, ContentPatterns.ANY_LINK),
)
CORE_PATTERN: Sequence[tuple[str, re.Pattern[str]]] = (
    (Crit.Content.BLOCKQUOTE, ContentPatterns.BLOCKQUOTE),
    (Crit.Content.DRAW, ContentPatterns.DRAW),
    (Crit.Content.DYNAMIC_VAR, ContentPatterns.DYNAMIC_VARIABLE),
    (Crit.Content.FLASHCARD, ContentPatterns.FLASHCARD),
    (Crit.Content.PAGE_REF, ContentPatterns.PAGE_REFERENCE),
    (Crit.Content.TAG, ContentPatterns.TAG),
    (Crit.Content.TAGGED_BACKLINK, ContentPatterns.TAGGED_BACKLINK),
)
RAW_PATTERN: Sequence[tuple[str, re.Pattern[str]]] = (
    (Crit.Content.INLINE_CODE, ContentPatterns.INLINE_CODE),
    (Crit.Content.ANY_LINK, ContentPatterns.ANY_LINK),
    (Crit.Content.ASSET, ContentPatterns.ASSET),
)
