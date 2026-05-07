"""Hierarchical patterns for elements."""

import re
from typing import TYPE_CHECKING, ClassVar

from logseq_analyzer.utils.enums import CritAdvCmd, CritCode, CritDblCurly, CritDblParen, CritEmb, CritExt

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
_URL = (
    r"(?:(?:https?|ftp)://)"
    r"(?:\S+(?::\S*)?@)?"
    r"(?:\d{1,3}(?:\.\d{1,3}){3}|\[[0-9A-F:]+\]|(?:[A-Z0-9-]+\.)+[A-Z]{2,})"
    r"(?::\d{2,5})?(?:/[^\s]*)?"
)


def _advcmd(key: str, variant: str = "") -> re.Pattern:
    """Create regex patterns for advanced commands."""
    suffix = rf"{key}\s{1}{variant}" if variant else key
    return re.compile(
        rf"#\+BEGIN_{suffix}.*?#\+END_{suffix}.*?(?:\n|$)",
        re.DOTALL | re.IGNORECASE,
    )


def _dblcurly(key: str) -> re.Pattern:
    """Create regex patterns for double curly braces."""
    return re.compile(
        rf"\{{\{{{key} .*?\}}\}}",
        re.IGNORECASE,
    )


def _internet_link(*, embedded: bool) -> re.Pattern:
    prefix = r"\!\[.*?\]" if embedded else r"(?<!\!)\[.*?\]"
    return re.compile(
        rf'{prefix}\({_URL}(?:\s+["\'][^)]*["\'])?\)',
        re.IGNORECASE,
    )


class IPattern:
    """Base pattern class."""

    ALL: re.Pattern
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]]
    FALLBACK: str

    @classmethod
    def process_pattern_hierarchy(cls, content: str) -> Iterator[tuple[str, str]]:
        """Process a pattern hierarchy to create a mapping of patterns to their respective values.

        Args:
            content (str): The content to process.

        Yields:
            Iterator[tuple[str, str]]: A generator yielding key-value pairs of patterns and their values.

        """
        for match in cls.ALL.finditer(content):
            text = match.group(0)
            for criteria, pattern in cls.PATTERN_MAP.items():
                if pattern.search(text):
                    yield criteria, text
                    break
            else:
                yield cls.FALLBACK, text


class AdvCmdPatterns(IPattern):
    """Patterns for advanced commands in Logseq."""

    ALL = re.compile(r"#\+BEGIN_.*?#\+END_.*?(?:\n|$)", re.DOTALL | re.IGNORECASE)
    EXPORT = _advcmd("EXPORT")
    EXPORT_ASCII = _advcmd("EXPORT", "ascii")
    EXPORT_LATEX = _advcmd("EXPORT", "latex")
    CAUTION = _advcmd("CAUTION")
    CENTER = _advcmd("CENTER")
    COMMENT = _advcmd("COMMENT")
    EXAMPLE = _advcmd("EXAMPLE")
    IMPORTANT = _advcmd("IMPORTANT")
    NOTE = _advcmd("NOTE")
    PINNED = _advcmd("PINNED")
    QUERY = _advcmd("QUERY")
    QUOTE = _advcmd("QUOTE")
    TIP = _advcmd("TIP")
    VERSE = _advcmd("VERSE")
    WARNING = _advcmd("WARNING")
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritAdvCmd.EXPORT_ASCII: EXPORT_ASCII,
        CritAdvCmd.EXPORT_LATEX: EXPORT_LATEX,
        CritAdvCmd.EXPORT: EXPORT,
        CritAdvCmd.CAUTION: CAUTION,
        CritAdvCmd.CENTER: CENTER,
        CritAdvCmd.COMMENT: COMMENT,
        CritAdvCmd.EXAMPLE: EXAMPLE,
        CritAdvCmd.IMPORTANT: IMPORTANT,
        CritAdvCmd.NOTE: NOTE,
        CritAdvCmd.PINNED: PINNED,
        CritAdvCmd.QUERY: QUERY,
        CritAdvCmd.QUOTE: QUOTE,
        CritAdvCmd.TIP: TIP,
        CritAdvCmd.VERSE: VERSE,
        CritAdvCmd.WARNING: WARNING,
    }
    FALLBACK = CritAdvCmd.ALL


class CodePatterns(IPattern):
    """Patterns for code blocks in Logseq."""

    ALL = re.compile(r"```.*?```", re.DOTALL | re.IGNORECASE)
    INLINE_CODE_BLOCK = re.compile(r"`[^`].+?`", re.IGNORECASE)
    MULTILINE_CODE_LANG = re.compile(r"```\w+.*?```", re.DOTALL | re.IGNORECASE)
    MULTILINE_CALC_BLOCK = re.compile(r"```calc.*?```", re.DOTALL | re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritCode.ML_CALC: MULTILINE_CALC_BLOCK,
        CritCode.ML_LANG: MULTILINE_CODE_LANG,
    }
    FALLBACK = CritCode.ML_ALL


class DoubleCurlyPatterns(IPattern):
    """Patterns for double curly braces in Logseq."""

    ALL = re.compile(r"\{\{.*?\}\}", re.IGNORECASE)
    EMBED = _dblcurly("embed")
    PAGE_EMBED = re.compile(r"\{\{embed \[\[.*?\]\]\}\}", re.IGNORECASE)
    BLOCK_EMBED = re.compile(rf"\{{\{{embed \(\({_UUID}\)\)\}}\}}", re.IGNORECASE)
    NAMESPACE_QUERY = _dblcurly("namespace")
    CARD = _dblcurly("cards")
    CLOZE = _dblcurly("cloze")
    SIMPLE_QUERY = _dblcurly("query")
    QUERY_FUNCTION = _dblcurly("function")
    EMBED_VIDEO_URL = _dblcurly("video")
    EMBED_TWITTER_TWEET = _dblcurly("tweet")
    EMBED_YOUTUBE_TIMESTAMP = _dblcurly("youtube-timestamp")
    RENDERER = _dblcurly("renderer")
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritDblCurly.PAGE_EMBEDS: PAGE_EMBED,
        CritDblCurly.BLOCK_EMBEDS: BLOCK_EMBED,
        CritDblCurly.EMBEDS: EMBED,
        CritDblCurly.NAMESPACE_QUERIES: NAMESPACE_QUERY,
        CritDblCurly.CARDS: CARD,
        CritDblCurly.CLOZES: CLOZE,
        CritDblCurly.SIMPLE_QUERIES: SIMPLE_QUERY,
        CritDblCurly.QUERY_FUNCTIONS: QUERY_FUNCTION,
        CritDblCurly.VIDEO_URLS: EMBED_VIDEO_URL,
        CritDblCurly.TWITTER_TWEETS: EMBED_TWITTER_TWEET,
        CritDblCurly.YOUTUBE_TIMESTAMPS: EMBED_YOUTUBE_TIMESTAMP,
        CritDblCurly.RENDERERS: RENDERER,
    }
    FALLBACK = CritDblCurly.ALL


class DoubleParenthesesPatterns(IPattern):
    """Patterns for double parentheses in Logseq."""

    ALL = re.compile(r"(?<!\{\{embed )\(\(.*?\)\)", re.IGNORECASE)
    BLOCK_REFERENCE = re.compile(rf"(?<!\{{\{{embed )\(\({_UUID}\)\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritDblParen.BLOCK_REFS: BLOCK_REFERENCE,
    }
    FALLBACK = CritDblParen.ALL_REFS


class EmbeddedLinkPatterns(IPattern):
    """Patterns for embedded links in Logseq."""

    ALL = re.compile(r"\!\[.*?\]\(.*?\)", re.IGNORECASE)
    INTERNET = _internet_link(embedded=True)
    ASSET = re.compile(r"\!\[.*?\]\(.*?assets/.*?\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritEmb.INTERNET: INTERNET,
        CritEmb.ASSET: ASSET,
    }
    FALLBACK = CritEmb.OTHER


class ExternalLinkPatterns(IPattern):
    """Patterns for external links in Logseq."""

    ALL = re.compile(r"(?<!\!)\[.*?\]\(.*?\)", re.IGNORECASE)
    INTERNET = _internet_link(embedded=False)
    ALIAS = re.compile(r"(?<!\!)\[.*?\]\([\[\[|\(\(].*?[\]\]|\)\)].*?\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritExt.INTERNET: INTERNET,
        CritExt.ALIAS: ALIAS,
    }
    FALLBACK = CritExt.OTHER


PATTERNS: Sequence[type[IPattern]] = (
    AdvCmdPatterns,
    CodePatterns,
    DoubleCurlyPatterns,
    DoubleParenthesesPatterns,
    EmbeddedLinkPatterns,
    ExternalLinkPatterns,
)
