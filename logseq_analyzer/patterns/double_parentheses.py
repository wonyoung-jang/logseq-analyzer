"""Double parentheses patterns for Logseq."""

import re

from ..utils.enums import CritDblParen

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
    BLOCK_REFERENCE: CritDblParen.BLOCK_REFS,
}

FALLBACK = CritDblParen.ALL_REFS
