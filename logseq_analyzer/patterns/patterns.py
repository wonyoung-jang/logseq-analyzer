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
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritAdvCmd.EXPORT: _advcmd("EXPORT"),
        CritAdvCmd.EXPORT_ASCII: _advcmd("EXPORT", "ascii"),
        CritAdvCmd.EXPORT_LATEX: _advcmd("EXPORT", "latex"),
        CritAdvCmd.CAUTION: _advcmd("CAUTION"),
        CritAdvCmd.CENTER: _advcmd("CENTER"),
        CritAdvCmd.COMMENT: _advcmd("COMMENT"),
        CritAdvCmd.EXAMPLE: _advcmd("EXAMPLE"),
        CritAdvCmd.IMPORTANT: _advcmd("IMPORTANT"),
        CritAdvCmd.NOTE: _advcmd("NOTE"),
        CritAdvCmd.PINNED: _advcmd("PINNED"),
        CritAdvCmd.QUERY: _advcmd("QUERY"),
        CritAdvCmd.QUOTE: _advcmd("QUOTE"),
        CritAdvCmd.TIP: _advcmd("TIP"),
        CritAdvCmd.VERSE: _advcmd("VERSE"),
        CritAdvCmd.WARNING: _advcmd("WARNING"),
    }
    FALLBACK = CritAdvCmd.ALL


class CodePatterns(IPattern):
    """Patterns for code blocks in Logseq."""

    ALL = re.compile(r"```.*?```", re.DOTALL | re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritCode.ML_CALC: re.compile(r"```calc.*?```", re.DOTALL | re.IGNORECASE),
        CritCode.ML_LANG: re.compile(r"```\w+.*?```", re.DOTALL | re.IGNORECASE),
    }
    FALLBACK = CritCode.ML_ALL


class DoubleCurlyPatterns(IPattern):
    """Patterns for double curly braces in Logseq."""

    ALL = re.compile(r"\{\{.*?\}\}", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritDblCurly.EMBED: _dblcurly("embed"),
        CritDblCurly.PAGE_EMBED: re.compile(r"\{\{embed \[\[.*?\]\]\}\}", re.IGNORECASE),
        CritDblCurly.BLOCK_EMBED: re.compile(rf"\{{\{{embed \(\({_UUID}\)\)\}}\}}", re.IGNORECASE),
        CritDblCurly.NAMESPACE_QUERY: _dblcurly("namespace"),
        CritDblCurly.CARD: _dblcurly("cards"),
        CritDblCurly.CLOZE: _dblcurly("cloze"),
        CritDblCurly.SIMPLE_QUERY: _dblcurly("query"),
        CritDblCurly.QUERY_FUNCTION: _dblcurly("function"),
        CritDblCurly.EMBED_VIDEO_URL: _dblcurly("video"),
        CritDblCurly.EMBED_TWITTER_TWEET: _dblcurly("tweet"),
        CritDblCurly.YOUTUBE_TIMESTAMP: _dblcurly("youtube-timestamp"),
        CritDblCurly.RENDERER: _dblcurly("renderer"),
    }
    FALLBACK = CritDblCurly.ALL


class DoubleParenthesesPatterns(IPattern):
    """Patterns for double parentheses in Logseq."""

    ALL = re.compile(r"(?<!\{\{embed )\(\(.*?\)\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritDblParen.BLOCK_REFS: re.compile(rf"(?<!\{{\{{embed )\(\({_UUID}\)\)", re.IGNORECASE),
    }
    FALLBACK = CritDblParen.ALL_REFS


class EmbeddedLinkPatterns(IPattern):
    """Patterns for embedded links in Logseq."""

    ALL = re.compile(r"\!\[.*?\]\(.*?\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritEmb.INTERNET: _internet_link(embedded=True),
        CritEmb.ASSET: re.compile(r"\!\[.*?\]\(.*?assets/.*?\)", re.IGNORECASE),
    }
    FALLBACK = CritEmb.OTHER


class ExternalLinkPatterns(IPattern):
    """Patterns for external links in Logseq."""

    ALL = re.compile(r"(?<!\!)\[.*?\]\(.*?\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritExt.INTERNET: _internet_link(embedded=False),
        CritExt.ALIAS: re.compile(r"(?<!\!)\[.*?\]\([\[\[|\(\(].*?[\]\]|\)\)].*?\)", re.IGNORECASE),
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
