"""Code patterns for Logseq."""

import re

from ..utils.enums import CritCode

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
    CALC_BLOCK: CritCode.ML_CALC,
    MULTILINE_CODE_LANG: CritCode.ML_LANG,
}

FALLBACK = CritCode.ML_ALL
