"""Hierarchical patterns for elements."""

import re
from typing import TYPE_CHECKING, ClassVar

from logseq_analyzer.utils.enums import Crit

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
URL = (
    r"(?:(?:https?|ftp)://)"
    r"(?:\S+(?::\S*)?@)?"
    r"(?:\d{1,3}(?:\.\d{1,3}){3}|\[[0-9A-F:]+\]|(?:[A-Z0-9-]+\.)+[A-Z]{2,})"
    r"(?::\d{2,5})?(?:/[^\s]*)?"
)


class ContentPatterns:
    """Class to hold compiled regex patterns for Logseq content."""

    BULLET = re.compile(r"^\s*-\s*", re.MULTILINE | re.IGNORECASE)
    PAGE_REFERENCE = re.compile(r"(?<!#)\[\[(.+?)\]\]", re.IGNORECASE)
    TAGGED_BACKLINK = re.compile(r"#\[\[([^\]#]+?)\]\]", re.IGNORECASE)
    TAG = re.compile(r"#(?!\[\[)([^\]#\s]+?)(?=\s|$)", re.IGNORECASE)
    PROPERTY = re.compile(r"^(?!\s*-\s)\s*?([A-Za-z0-9_-]+?)(?=::)", re.MULTILINE | re.IGNORECASE)
    PROPERTY_VALUE = re.compile(r"^(?!\s*-\s)\s*?([A-Za-z0-9_-]+?)::(.*)$", re.MULTILINE | re.IGNORECASE)
    ASSET = re.compile(r"assets/(.+)", re.IGNORECASE)
    DRAW = re.compile(r"(?<!#)\[\[draws/(.+?)\.excalidraw\]\]", re.IGNORECASE)
    BLOCKQUOTE = re.compile(r"(?:^|\s)-\ >.*", re.MULTILINE | re.IGNORECASE)
    FLASHCARD = re.compile(r"(?:^|\s)-\ .*#card|\[\[card\]\].*", re.MULTILINE | re.IGNORECASE)
    DYNAMIC_VARIABLE = re.compile(r"<%\s*.*?\s*%>", re.IGNORECASE)
    ANY_LINK = re.compile(rf"\b(?:{URL})\b", re.IGNORECASE)
    INLINE_CODE_BLOCK = re.compile(r"`[^`].+?`", re.IGNORECASE)


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
        rf'{prefix}\({URL}(?:\s+["\'][^)]*["\'])?\)',
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
        Crit.AdvCmd.EXPORT: _advcmd("EXPORT"),
        Crit.AdvCmd.EXPORT_ASCII: _advcmd("EXPORT", "ascii"),
        Crit.AdvCmd.EXPORT_LATEX: _advcmd("EXPORT", "latex"),
        Crit.AdvCmd.CAUTION: _advcmd("CAUTION"),
        Crit.AdvCmd.CENTER: _advcmd("CENTER"),
        Crit.AdvCmd.COMMENT: _advcmd("COMMENT"),
        Crit.AdvCmd.EXAMPLE: _advcmd("EXAMPLE"),
        Crit.AdvCmd.IMPORTANT: _advcmd("IMPORTANT"),
        Crit.AdvCmd.NOTE: _advcmd("NOTE"),
        Crit.AdvCmd.PINNED: _advcmd("PINNED"),
        Crit.AdvCmd.QUERY: _advcmd("QUERY"),
        Crit.AdvCmd.QUOTE: _advcmd("QUOTE"),
        Crit.AdvCmd.TIP: _advcmd("TIP"),
        Crit.AdvCmd.VERSE: _advcmd("VERSE"),
        Crit.AdvCmd.WARNING: _advcmd("WARNING"),
    }
    FALLBACK = Crit.AdvCmd.ALL


class CodePatterns(IPattern):
    """Patterns for code blocks in Logseq."""

    ALL = re.compile(r"```.*?```", re.DOTALL | re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        Crit.Code.ML_CALC: re.compile(r"```calc.*?```", re.DOTALL | re.IGNORECASE),
        Crit.Code.ML_LANG: re.compile(r"```\w+.*?```", re.DOTALL | re.IGNORECASE),
    }
    FALLBACK = Crit.Code.ML_ALL


class DoubleCurlyPatterns(IPattern):
    """Patterns for double curly braces in Logseq."""

    ALL = re.compile(r"\{\{.*?\}\}", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        Crit.DblCurly.EMBED: _dblcurly("embed"),
        Crit.DblCurly.PAGE_EMBED: re.compile(r"\{\{embed \[\[.*?\]\]\}\}", re.IGNORECASE),
        Crit.DblCurly.BLOCK_EMBED: re.compile(rf"\{{\{{embed \(\({_UUID}\)\)\}}\}}", re.IGNORECASE),
        Crit.DblCurly.NAMESPACE_QUERY: _dblcurly("namespace"),
        Crit.DblCurly.CARD: _dblcurly("cards"),
        Crit.DblCurly.CLOZE: _dblcurly("cloze"),
        Crit.DblCurly.SIMPLE_QUERY: _dblcurly("query"),
        Crit.DblCurly.QUERY_FUNCTION: _dblcurly("function"),
        Crit.DblCurly.EMBED_VIDEO_URL: _dblcurly("video"),
        Crit.DblCurly.EMBED_TWITTER_TWEET: _dblcurly("tweet"),
        Crit.DblCurly.YOUTUBE_TIMESTAMP: _dblcurly("youtube-timestamp"),
        Crit.DblCurly.RENDERER: _dblcurly("renderer"),
    }
    FALLBACK = Crit.DblCurly.ALL


class DoubleParenthesesPatterns(IPattern):
    """Patterns for double parentheses in Logseq."""

    ALL = re.compile(r"(?<!\{\{embed )\(\(.*?\)\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        Crit.DblParen.BLOCK_REFS: re.compile(rf"(?<!\{{\{{embed )\(\({_UUID}\)\)", re.IGNORECASE),
    }
    FALLBACK = Crit.DblParen.ALL_REFS


class EmbeddedLinkPatterns(IPattern):
    """Patterns for embedded links in Logseq."""

    ALL = re.compile(r"\!\[.*?\]\(.*?\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        Crit.Emb.INTERNET: _internet_link(embedded=True),
        Crit.Emb.ASSET: re.compile(r"\!\[.*?\]\(.*?assets/.*?\)", re.IGNORECASE),
    }
    FALLBACK = Crit.Emb.OTHER


class ExternalLinkPatterns(IPattern):
    """Patterns for external links in Logseq."""

    ALL = re.compile(r"(?<!\!)\[.*?\]\(.*?\)", re.IGNORECASE)
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        Crit.Ext.INTERNET: _internet_link(embedded=False),
        Crit.Ext.ALIAS: re.compile(r"(?<!\!)\[.*?\]\([\[\[|\(\(].*?[\]\]|\)\)].*?\)", re.IGNORECASE),
    }
    FALLBACK = Crit.Ext.OTHER


PATTERNS: Sequence[type[IPattern]] = (
    AdvCmdPatterns,
    CodePatterns,
    DoubleCurlyPatterns,
    DoubleParenthesesPatterns,
    EmbeddedLinkPatterns,
    ExternalLinkPatterns,
)
RAW_DATA_MAP: dict[str, re.Pattern[str]] = {
    Crit.Code.INLINE: ContentPatterns.INLINE_CODE_BLOCK,
    Crit.Content.ANY_LINKS: ContentPatterns.ANY_LINK,
    Crit.Content.ASSETS: ContentPatterns.ASSET,
}
PRIMARY_DATA_MAP: dict[str, re.Pattern[str]] = {
    Crit.Content.BLOCKQUOTES: ContentPatterns.BLOCKQUOTE,
    Crit.Content.DRAW: ContentPatterns.DRAW,
    Crit.Content.FLASHCARD: ContentPatterns.FLASHCARD,
    Crit.Content.PAGE_REF: ContentPatterns.PAGE_REFERENCE,
    Crit.Content.TAGGED_BACKLINK: ContentPatterns.TAGGED_BACKLINK,
    Crit.Content.TAG: ContentPatterns.TAG,
    Crit.Content.DYNAMIC_VAR: ContentPatterns.DYNAMIC_VARIABLE,
}
MASK_MAP: dict[str, re.Pattern[str]] = {
    Crit.Code.ML_ALL: CodePatterns.ALL,
    Crit.Code.INLINE: ContentPatterns.INLINE_CODE_BLOCK,
    Crit.AdvCmd.ALL: AdvCmdPatterns.ALL,
    Crit.Content.ANY_LINKS: ContentPatterns.ANY_LINK,
}
