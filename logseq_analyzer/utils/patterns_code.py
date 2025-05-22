"""Code patterns for Logseq."""

import re
from collections import defaultdict
from typing import Iterator

from .enums import Criteria

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

CALC_BLOCK = re.compile(
    r"""
    ```calc             # Three backticks followed by "calc"
    .*?                 # Any characters (non-greedy)
    ```                 # Three backticks
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

PATTERN_MAP = {
    CALC_BLOCK: Criteria.CALC_BLOCKS.value,
    MULTILINE_CODE_LANG: Criteria.MULTILINE_CODE_LANGS.value,
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
            output[Criteria.MULTILINE_CODE_BLOCKS.value].append(text)

    return output
