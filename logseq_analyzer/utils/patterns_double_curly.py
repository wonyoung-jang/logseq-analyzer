"""Double curly patterns for Logseq."""

import re
from collections import defaultdict
from typing import Iterator

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
    PAGE_EMBED: Criteria.PAGE_EMBEDS.value,
    BLOCK_EMBED: Criteria.BLOCK_EMBEDS.value,
    EMBED: Criteria.EMBEDS.value,
    NAMESPACE_QUERY: Criteria.NAMESPACE_QUERIES.value,
    CARD: Criteria.CARDS.value,
    CLOZE: Criteria.CLOZES.value,
    SIMPLE_QUERY: Criteria.SIMPLE_QUERIES.value,
    QUERY_FUNCTION: Criteria.QUERY_FUNCTIONS.value,
    EMBED_VIDEO_URL: Criteria.EMBED_VIDEO_URLS.value,
    EMBED_TWITTER_TWEET: Criteria.EMBED_TWITTER_TWEETS.value,
    EMBED_YOUTUBE_TIMESTAMP: Criteria.EMBED_YOUTUBE_TIMESTAMPS.value,
    RENDERER: Criteria.RENDERERS.value,
}


def process(results: Iterator[re.Match[str]]) -> dict[str, list[str]]:
    """
    Process external links and categorize them.

    Args:
        Iterator[re.Match[str]]: Iterator of regex match objects for external links.

    Returns:
        dict[str, list[str]]: Dictionary categorizing external links.
    """
    output = defaultdict(list)

    for match in results:
        text = match.group(0)
        for pattern, criteria in PATTERN_MAP.items():
            if pattern.search(text):
                output[criteria].append(text)
                break
        else:
            output[Criteria.MACROS.value].append(text)

    return output
