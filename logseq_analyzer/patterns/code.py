"""Code patterns for Logseq."""

import re

from ..utils.enums import Criteria

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
    CALC_BLOCK: Criteria.COD_ML_CALC,
    MULTILINE_CODE_LANG: Criteria.COD_ML_LANG,
}

FALLBACK = Criteria.COD_ML_ALL
