"""External link patterns for Logseq."""

import re

from ..utils.enums import Criteria

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
    (?:(?:https?|ftp)://)                   #   scheme:// (http, https or ftp)
    (?:\S+(?::\S*)?@)?                      #   optional user:pass@
    (?:                                     
    \d{1,3}(?:\.\d{1,3}){3}             #   IPv4
    |
    \[[0-9A-F:]+\]                      #   IPv6 (in brackets)
    |
    (?:[A-Z0-9-]+\.)+[A-Z]{2,}          #   domain name
    )
    (?::\d{2,5})?                           #   optional port
    (?:/[^\s]*)?                            #   optional path/query/fragment
    )
    (?:\s+["\'][^)]*["\'])?\)             # Optional: space followed by quoted string
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

PATTERN_MAP = {
    INTERNET: Criteria.EXT_LINK_INTERNET.value,
    ALIAS: Criteria.EXT_LINK_ALIAS.value,
}

FALLBACK = Criteria.EXT_LINK_OTHER.value
