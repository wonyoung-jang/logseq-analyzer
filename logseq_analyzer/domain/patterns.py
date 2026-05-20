"""Hierarchical patterns for elements."""

import re
from typing import TYPE_CHECKING

from logseq_analyzer.domain.enums import Crit

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

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

    BULLET = re.compile(r"^\s*-\s*", re.MULTILINE | re.IGNORECASE)
    PAGE_REFERENCE = re.compile(r"(?<!#)\[\[(.+?)\]\]", re.IGNORECASE)
    TAGGED_BACKLINK = re.compile(r"#\[\[([^\]#]+?)\]\]", re.IGNORECASE)
    TAG = re.compile(r"#(?!\[\[)([^\]#\s]+)", re.IGNORECASE)
    PROPERTY = re.compile(r"^(?!\s*-\s)\s*([A-Za-z0-9_-]+)(?=::)", re.MULTILINE | re.IGNORECASE)
    PROPERTY_VALUE = re.compile(r"^(?!\s*-\s)\s*([A-Za-z0-9_-]+)::(.*)$", re.MULTILINE | re.IGNORECASE)
    ASSET = re.compile(r"assets/(?:.*/)?([^\s/]+\.\w{2,5})(?=\W|$)", re.IGNORECASE)
    DRAW = re.compile(r"(?<!#)\[\[draws/(.+?)\.excalidraw\]\]", re.IGNORECASE)
    BLOCKQUOTE = re.compile(r"(?!^[^\S\n])(- >.*)", re.MULTILINE | re.IGNORECASE)
    FLASHCARD = re.compile(r"(?!^[^\S\n])(- [^\n]*#card|\[\[card\]\].*)", re.MULTILINE | re.IGNORECASE)
    DYNAMIC_VARIABLE = re.compile(r"<%\s*.*?\s*%>", re.IGNORECASE)
    ANY_LINK = re.compile(rf"\b(?:{_URL})\b", re.IGNORECASE)
    INLINE_CODE_BLOCK = re.compile(r"`[^`].+?`", re.IGNORECASE)


def _advcmd(key: str, variant: str = "") -> re.Pattern:
    """Create regex patterns for advanced commands."""
    _key = rf"{key}\s{1}{variant}" if variant else key
    return re.compile(rf"#\+BEGIN_{_key}.*?#\+END_{_key}.*?(?:\n|$)", re.DOTALL | re.IGNORECASE)


def _mlcode(key: str) -> re.Pattern:
    """Create regex patterns for multiline code blocks."""
    return re.compile(rf"```{key}.*?```", re.DOTALL | re.IGNORECASE)


def _dblcurly(key: str, variant: str = "") -> re.Pattern:
    """Create regex patterns for double curly braces."""
    _key = rf"{key} " if key else ""
    suffix = variant or r".*?"
    return re.compile(rf"\{{\{{{_key}{suffix}\}}\}}", re.IGNORECASE)


def _dblparen(key: str) -> re.Pattern:
    """Create regex patterns for double parentheses."""
    _key = key or r".*?"
    return re.compile(rf"(?<!\{{\{{embed )\(\({_key}\)\)", re.IGNORECASE)


def _emblink(key: str) -> re.Pattern:
    """Create regex patterns for embedded links."""
    _key = key or r".*?"
    return re.compile(rf"\!\[.*?\]\({_key}\)", re.IGNORECASE)


def _extlink(key: str) -> re.Pattern:
    """Create regex patterns for external links."""
    _key = key or r".*?"
    return re.compile(rf"(?<!\!)\[.*?\]\({_key}\)", re.IGNORECASE)


class IPattern:
    """Base pattern class."""

    ALL: re.Pattern
    PATTERN: Sequence[tuple[str, re.Pattern]]
    FALLBACK: str

    @classmethod
    def process_hierarchy(cls, content: str) -> Iterator[tuple[str, str]]:
        """Process a pattern hierarchy to create a mapping of patterns to their respective values.

        Args:
            content (str): The content to process.

        Yields:
            Iterator[tuple[str, str]]: A generator yielding key-value pairs of patterns and their values.

        """
        for match in cls.ALL.finditer(content):
            value = match.group(0)
            for prefix, pattern in cls.PATTERN:
                if pattern.search(value):
                    yield prefix, value
                    break
            else:
                yield cls.FALLBACK, value


class AdvCmdPatterns(IPattern):
    """Patterns for advanced commands in Logseq."""

    ALL = _advcmd("")
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.AdvCmd.EXPORT, _advcmd("EXPORT")),
        (Crit.AdvCmd.EXPORT_ASCII, _advcmd("EXPORT", "ascii")),
        (Crit.AdvCmd.EXPORT_LATEX, _advcmd("EXPORT", "latex")),
        (Crit.AdvCmd.CAUTION, _advcmd("CAUTION")),
        (Crit.AdvCmd.CENTER, _advcmd("CENTER")),
        (Crit.AdvCmd.COMMENT, _advcmd("COMMENT")),
        (Crit.AdvCmd.EXAMPLE, _advcmd("EXAMPLE")),
        (Crit.AdvCmd.IMPORTANT, _advcmd("IMPORTANT")),
        (Crit.AdvCmd.NOTE, _advcmd("NOTE")),
        (Crit.AdvCmd.PINNED, _advcmd("PINNED")),
        (Crit.AdvCmd.QUERY, _advcmd("QUERY")),
        (Crit.AdvCmd.QUOTE, _advcmd("QUOTE")),
        (Crit.AdvCmd.TIP, _advcmd("TIP")),
        (Crit.AdvCmd.VERSE, _advcmd("VERSE")),
        (Crit.AdvCmd.WARNING, _advcmd("WARNING")),
    )
    FALLBACK = Crit.AdvCmd.ALL


class CodePatterns(IPattern):
    """Patterns for code blocks in Logseq."""

    ALL = _mlcode("")
    PATTERN: Sequence[tuple[str, re.Pattern]] = (
        (Crit.MultLineCode.CALC, _mlcode("calc")),
        (Crit.MultLineCode.LANGUAGE, _mlcode(r"\w+")),
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
        (Crit.ExtLink.ALIAS, _extlink(r"[\[\[|\(\(].*?[\]\]|\)\)].*?")),
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
    (Crit.Content.INLINE_CODE, ContentPatterns.INLINE_CODE_BLOCK),
    (Crit.AdvCmd.ALL, AdvCmdPatterns.ALL),
    (Crit.Content.ANY_LINK, ContentPatterns.ANY_LINK),
)
CORE_PATTERN: Sequence[tuple[str, re.Pattern[str]]] = (
    (Crit.Content.BLOCKQUOTE, ContentPatterns.BLOCKQUOTE),
    (Crit.Content.DRAW, ContentPatterns.DRAW),
    (Crit.Content.FLASHCARD, ContentPatterns.FLASHCARD),
    (Crit.Content.PAGE_REF, ContentPatterns.PAGE_REFERENCE),
    (Crit.Content.TAGGED_BACKLINK, ContentPatterns.TAGGED_BACKLINK),
    (Crit.Content.TAG, ContentPatterns.TAG),
    (Crit.Content.DYNAMIC_VAR, ContentPatterns.DYNAMIC_VARIABLE),
)
RAW_PATTERN: Sequence[tuple[str, re.Pattern[str]]] = (
    (Crit.Content.INLINE_CODE, ContentPatterns.INLINE_CODE_BLOCK),
    (Crit.Content.ANY_LINK, ContentPatterns.ANY_LINK),
    (Crit.Content.ASSET, ContentPatterns.ASSET),
)
