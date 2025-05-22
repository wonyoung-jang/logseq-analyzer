"""Double parentheses patterns for Logseq."""

import re
from collections import defaultdict
from typing import Iterator

from .enums import Criteria

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

PATTERN_MAP = {
    BLOCK_REFERENCE: Criteria.BLOCK_REFERENCES.value,
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
            output[Criteria.REFERENCES_GENERAL.value].append(text)

    return output
