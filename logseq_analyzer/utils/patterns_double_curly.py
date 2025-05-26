"""Double curly patterns for Logseq."""

import re

from .enums import Criteria

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
    PAGE_EMBED: Criteria.DBC_PAGE_EMBEDS.value,
    BLOCK_EMBED: Criteria.DBC_BLOCK_EMBEDS.value,
    EMBED: Criteria.DBC_EMBEDS.value,
    NAMESPACE_QUERY: Criteria.DBC_NAMESPACE_QUERIES.value,
    CARD: Criteria.DBC_CARDS.value,
    CLOZE: Criteria.DBC_CLOZES.value,
    SIMPLE_QUERY: Criteria.DBC_SIMPLE_QUERIES.value,
    QUERY_FUNCTION: Criteria.DBC_QUERY_FUNCTIONS.value,
    EMBED_VIDEO_URL: Criteria.DBC_VIDEO_URLS.value,
    EMBED_TWITTER_TWEET: Criteria.DBC_TWITTER_TWEETS.value,
    EMBED_YOUTUBE_TIMESTAMP: Criteria.DBC_YOUTUBE_TIMESTAMPS.value,
    RENDERER: Criteria.DBC_RENDERERS.value,
}

FALLBACK = Criteria.DBC_ALL.value
