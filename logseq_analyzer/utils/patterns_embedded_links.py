"""Embedded link patterns for Logseq."""

import re

from .enums import Criteria

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

ASSET = re.compile(
    r"""
    \!\[.*?\]               # ![...]
    \(                      # Opening parenthesis
    .*?                     # Any characters (non-greedy)
        assets/             # Literal "assets/" 
        |
        \.\.assets/         # or "..assets/"
    .*?                     # Any characters (non-greedy)
    \)                      # Closing parenthesis
    """,
    re.IGNORECASE | re.VERBOSE,
)

PATTERN_MAP = {
    INTERNET: Criteria.EMBEDDED_LINKS_INTERNET.value,
    ASSET: Criteria.EMBEDDED_LINKS_ASSET.value,
}
