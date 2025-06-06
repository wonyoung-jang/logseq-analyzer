"""Double curly patterns for Logseq."""

import re

from ..utils.enums import CritDblCurly

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

PATTERN_MAP = {
    PAGE_EMBED: CritDblCurly.PAGE_EMBEDS,
    BLOCK_EMBED: CritDblCurly.BLOCK_EMBEDS,
    EMBED: CritDblCurly.EMBEDS,
    NAMESPACE_QUERY: CritDblCurly.NAMESPACE_QUERIES,
    CARD: CritDblCurly.CARDS,
    CLOZE: CritDblCurly.CLOZES,
    SIMPLE_QUERY: CritDblCurly.SIMPLE_QUERIES,
    QUERY_FUNCTION: CritDblCurly.QUERY_FUNCTIONS,
    EMBED_VIDEO_URL: CritDblCurly.VIDEO_URLS,
    EMBED_TWITTER_TWEET: CritDblCurly.TWITTER_TWEETS,
    EMBED_YOUTUBE_TIMESTAMP: CritDblCurly.YOUTUBE_TIMESTAMPS,
    RENDERER: CritDblCurly.RENDERERS,
}

FALLBACK = CritDblCurly.ALL
