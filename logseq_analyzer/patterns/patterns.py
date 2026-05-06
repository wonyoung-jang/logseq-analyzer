"""Hierarchical patterns for elements."""

import re
from typing import TYPE_CHECKING, ClassVar

from logseq_analyzer.utils.enums import CritAdvCmd, CritCode, CritDblCurly, CritDblParen, CritEmb, CritExt

if TYPE_CHECKING:
    from collections.abc import Iterator


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

    ALL = re.compile(
        r"""
        \#\+BEGIN_          # "#+BEGIN_"
        .*?                 # Any characters (non-greedy)
        \#\+END_            # "#+END_"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    EXPORT = re.compile(
        r"""
        \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT"
        .*?                 # Any characters (non-greedy)
        \#\+END_EXPORT      # "#+END_EXPORT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    EXPORT_ASCII = re.compile(
        r"""
        \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT ascii"
        \s{1}               # Single space
        ascii               # "ascii"
        .*?                 # Any characters (non-greedy)
        \#\+END_EXPORT      # "#+END_EXPORT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    EXPORT_LATEX = re.compile(
        r"""
        \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT latex"
        \s{1}               # Single space
        latex               # "latex"
        .*?                 # Any characters (non-greedy)
        \#\+END_EXPORT      # "#+END_EXPORT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    CAUTION = re.compile(
        r"""
        \#\+BEGIN_CAUTION   # "#+BEGIN_CAUTION"
        .*?                 # Any characters (non-greedy)
        \#\+END_CAUTION     # "#+END_CAUTION"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    CENTER = re.compile(
        r"""
        \#\+BEGIN_CENTER    # "#+BEGIN_CENTER"
        .*?                 # Any characters (non-greedy)
        \#\+END_CENTER      # "#+END_CENTER"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    COMMENT = re.compile(
        r"""
        \#\+BEGIN_COMMENT   # "#+BEGIN_COMMENT"
        .*?                 # Any characters (non-greedy)
        \#\+END_COMMENT     # "#+END_COMMENT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    EXAMPLE = re.compile(
        r"""
        \#\+BEGIN_EXAMPLE   # "#+BEGIN_EXAMPLE"
        .*?                 # Any characters (non-greedy)
        \#\+END_EXAMPLE     # "#+END_EXAMPLE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    IMPORTANT = re.compile(
        r"""
        \#\+BEGIN_IMPORTANT # "#+BEGIN_IMPORTANT"
        .*?                 # Any characters (non-greedy)
        \#\+END_IMPORTANT   # "#+END_IMPORTANT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    NOTE = re.compile(
        r"""
        \#\+BEGIN_NOTE      # "#+BEGIN_NOTE"
        .*?                 # Any characters (non-greedy)
        \#\+END_NOTE        # "#+END_NOTE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    PINNED = re.compile(
        r"""
        \#\+BEGIN_PINNED    # "#+BEGIN_PINNED"
        .*?                 # Any characters (non-greedy)
        \#\+END_PINNED      # "#+END_PINNED"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    QUERY = re.compile(
        r"""
        \#\+BEGIN_QUERY     # "#+BEGIN_QUERY"
        .*?                 # Any characters (non-greedy)
        \#\+END_QUERY       # "#+END_QUERY"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    QUOTE = re.compile(
        r"""
        \#\+BEGIN_QUOTE     # "#+BEGIN_QUOTE"
        .*?                 # Any characters (non-greedy)
        \#\+END_QUOTE       # "#+END_QUOTE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    TIP = re.compile(
        r"""
        \#\+BEGIN_TIP       # "#+BEGIN_TIP"
        .*?                 # Any characters (non-greedy)
        \#\+END_TIP         # "#+END_TIP"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    VERSE = re.compile(
        r"""
        \#\+BEGIN_VERSE     # "#+BEGIN_VERSE"
        .*?                 # Any characters (non-greedy)
        \#\+END_VERSE       # "#+END_VERSE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    WARNING = re.compile(
        r"""
        \#\+BEGIN_WARNING   # "#+BEGIN_WARNING"
        .*?                 # Any characters (non-greedy)
        \#\+END_WARNING     # "#+END_WARNING"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
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

    ALL = re.compile(
        r"""
        ```                 # Three backticks
        .*?                 # Any characters (non-greedy)
        ```                 # Three backticks
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    INLINE_CODE_BLOCK = re.compile(
        r"""
        `                   # One backtick
        [^`].+?             # Any characters except backtick (non-greedy)
        `                   # One backtick
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    MULTILINE_CODE_LANG = re.compile(
        r"""
        ```                 # Three backticks
        \w+                 # One or more word characters
        .*?                 # Any characters (non-greedy)
        ```                 # Three backticks
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    MULTILINE_CALC_BLOCK = re.compile(
        r"""
        ```calc             # Three backticks followed by "calc"
        .*?                 # Any characters (non-greedy)
        ```                 # Three backticks
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritCode.ML_CALC: MULTILINE_CALC_BLOCK,
        CritCode.ML_LANG: MULTILINE_CODE_LANG,
    }
    FALLBACK = CritCode.ML_ALL


class DoubleCurlyPatterns(IPattern):
    """Patterns for double curly braces in Logseq."""

    ALL = re.compile(
        r"""
        \{\{                # Opening double braces
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    EMBED = re.compile(
        r"""
        \{\{embed\          # "{{embed" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    PAGE_EMBED = re.compile(
        r"""
        \{\{embed\          # "{{embed" followed by space
        \[\[                # Opening double brackets
        .*?                 # Any characters (non-greedy)
        \]\]                # Closing double brackets
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    BLOCK_EMBED = re.compile(
        r"""
        \{\{embed\          # "{{embed" followed by space
        \(\(                # Opening double parentheses
        [0-9a-f]{8}-        # 8 hex digits followed by hyphen
        [0-9a-f]{4}-        # 4 hex digits followed by hyphen
        [0-9a-f]{4}-        # 4 hex digits followed by hyphen
        [0-9a-f]{4}-        # 4 hex digits followed by hyphen
        [0-9a-f]{12}        # 12 hex digits
        \)\)                # Closing double parentheses
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    NAMESPACE_QUERY = re.compile(
        r"""
        \{\{namespace\      # "{{namespace" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    CARD = re.compile(
        r"""
        \{\{cards\          # "{{cards" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    CLOZE = re.compile(
        r"""
        \{\{cloze\          # "{{cloze" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    SIMPLE_QUERY = re.compile(
        r"""
        \{\{query\          # "{{query" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    QUERY_FUNCTION = re.compile(
        r"""
        \{\{function\       # "{{function" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    EMBED_VIDEO_URL = re.compile(
        r"""
        \{\{video\          # "{{video" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    EMBED_TWITTER_TWEET = re.compile(
        r"""
        \{\{tweet\          # "{{tweet" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    EMBED_YOUTUBE_TIMESTAMP = re.compile(
        r"""
        \{\{youtube-timestamp\  # "{{youtube-timestamp" followed by space
        .*?                     # Any characters (non-greedy)
        \}\}                    # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    RENDERER = re.compile(
        r"""
        \{\{renderer\       # "{{renderer" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
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

    ALL = re.compile(
        r"""
        (?<!\{\{embed\ )    # Negative lookbehind: not preceded by "{{embed "
        \(\(                # Opening double parentheses
        .*?                 # Any characters (non-greedy)
        \)\)                # Closing double parentheses
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    BLOCK_REFERENCE = re.compile(
        r"""
        (?<!\{\{embed\ )    # Negative lookbehind: not preceded by "{{embed "
        \(\(                # Opening double parentheses
        [0-9a-f]{8}-        # 8 hex digits followed by hyphen
        [0-9a-f]{4}-        # 4 hex digits followed by hyphen
        [0-9a-f]{4}-        # 4 hex digits followed by hyphen
        [0-9a-f]{4}-        # 4 hex digits followed by hyphen
        [0-9a-f]{12}        # 12 hex digits
        \)\)                # Closing double parentheses
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritDblParen.BLOCK_REFS: BLOCK_REFERENCE,
    }
    FALLBACK = CritDblParen.ALL_REFS


class EmbeddedLinkPatterns(IPattern):
    """Patterns for embedded links in Logseq."""

    ALL = re.compile(
        r"""
        \!\[.*?\]           # ![...]
        \(.*?\)             # (...)
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    INTERNET = re.compile(
        r"""
        \!\[.*?\]           # ![...]
        \(                  # Opening parenthesis
        (
        (?:(?:https?|ftp)://)               #   scheme:// (http, https or ftp)
        (?:\S+(?::\S*)?@)?                  #   optional user:pass@
        (?:
        \d{1,3}(?:\.\d{1,3}){3}             #   IPv4
        |
        \[[0-9A-F:]+\]                      #   IPv6 (in brackets)
        |
        (?:[A-Z0-9-]+\.)+[A-Z]{2,}          #   domain name
        )
        (?::\d{2,5})?                       #   optional port
        (?:/[^\s]*)?                        #   optional path/query/fragment
        )
        (?:\s+["\'][^)]*["\'])?\)           # Optional: space followed by quoted string
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    ASSET = re.compile(
        r"""
        \!\[.*?\]               # ![...]
        \(                      # Opening parenthesis
        .*?                     # Any characters (non-greedy)
        assets/                 # Literal "assets/"
        .*?                     # Any characters (greedy)
        \)
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritEmb.INTERNET: INTERNET,
        CritEmb.ASSET: ASSET,
    }
    FALLBACK = CritEmb.OTHER


class ExternalLinkPatterns(IPattern):
    """Patterns for external links in Logseq."""

    ALL = re.compile(
        r"""
        (?<!\!)             # Negative lookbehind: not preceded by !
        \[.*?\]             # [...]
        \(.*?\)             # (...)
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    INTERNET = re.compile(
        r"""
        (?<!\!)             # Negative lookbehind: not preceded by !
        \[.*?\]             # [...]
        \(                  # Opening parenthesis
        (
        (?:(?:https?|ftp)://)               #   scheme:// (http, https or ftp)
        (?:\S+(?::\S*)?@)?                  #   optional user:pass@
        (?:
        \d{1,3}(?:\.\d{1,3}){3}             #   IPv4
        |
        \[[0-9A-F:]+\]                      #   IPv6 (in brackets)
        |
        (?:[A-Z0-9-]+\.)+[A-Z]{2,}          #   domain name
        )
        (?::\d{2,5})?                       #   optional port
        (?:/[^\s]*)?                        #   optional path/query/fragment
        )
        (?:\s+["\'][^)]*["\'])?\)           # Optional: space followed by quoted string
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    ALIAS = re.compile(
        r"""
        (?<!\!)             # Negative lookbehind: not preceded by !
        \[.*?\]             # [...]
        \(                  # Opening parenthesis
        [\[\[|\(\(]         # Either [[ or ((
        .*?                 # Any characters (non-greedy)
        [\]\]|\)\)]         # Either ]] or ))
        .*?                 # Any characters (non-greedy)
        \)                  # Closing parenthesis
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    PATTERN_MAP: ClassVar[dict[str, re.Pattern]] = {
        CritExt.INTERNET: INTERNET,
        CritExt.ALIAS: ALIAS,
    }
    FALLBACK = CritExt.OTHER
