"""
Compile frequently used regex patterns for Logseq content.
"""

import re

BULLET = re.compile(
    r"""
    ^           # Beginning of line
    \s*         # Optional whitespace
    -           # Literal hyphen
    \s*         # Optional whitespace
    """,
    re.MULTILINE | re.IGNORECASE | re.VERBOSE,
)

PAGE_REFERENCE = re.compile(
    r"""
    (?<!\#)     # Negative lookbehind: not preceded by #
    \[\[        # Opening double brackets
    (.+?)       # Capture group: the page name (non-greedy)
    \]\]        # Closing double brackets
    """,
    re.IGNORECASE | re.VERBOSE,
)

TAGGED_BACKLINK = re.compile(
    r"""
    \#          # Hash character
    \[\[        # Opening double brackets
    ([^\]\#]+?) # Anything except closing brackets or hash (non-greedy)
    \]\]        # Closing double brackets
    """,
    re.IGNORECASE | re.VERBOSE,
)

TAG = re.compile(
    r"""
    \#              # Hash character
    (?!\[\[)        # Negative lookahead: not followed by [[
    ([^\]\#\s]+?)   # Anything except closing brackets, hash, or whitespace (non-greedy)
    (?=\s|$)        # Followed by whitespace or end of line
    """,
    re.IGNORECASE | re.VERBOSE,
)

PROPERTY = re.compile(
    r"""
    ^                   # Start of line
    (?!\s*-\s)          # Negative lookahead: not a bullet
    \s*?                # Optional whitespace
    ([A-Za-z0-9_-]+?)   # Capture group: alphanumeric, underscore, or hyphen (non-greedy)
    (?=::)              # Positive lookahead: double colon
    """,
    re.MULTILINE | re.IGNORECASE | re.VERBOSE,
)

PROPERTY_VALUE = re.compile(
    r"""
    ^                   # Start of line
    (?!\s*-\s)          # Negative lookahead: not a bullet
    \s*?                # Optional whitespace
    ([A-Za-z0-9_-]+?)   # Capture group 1: Alphanumeric, underscore, or hyphen (non-greedy)
    ::                  # Literal ::
    (.*)                # Capture group 2: Any characters
    $                   # End of line
    """,
    re.MULTILINE | re.IGNORECASE | re.VERBOSE,
)

ASSET = re.compile(
    r"""
    assets/         # assets/ literal string
    (.+)            # Capture group: anything except newline (non-greedy)
    """,
    re.IGNORECASE | re.VERBOSE,
)

DRAW = re.compile(
    r"""
    (?<!\#)             # Negative lookbehind: not preceded by #
    \[\[                # Opening double brackets
    draws/(.+?)         # Literal "draws/" followed by capture group
    \.excalidraw        # Literal ".excalidraw"
    \]\]                # Closing double brackets
    """,
    re.IGNORECASE | re.VERBOSE,
)

BLOCKQUOTE = re.compile(
    r"""
    (?:^|\s)            # Start of line or whitespace
    -\ >                # Hyphen, space, greater than
    .*                  # Any characters
    """,
    re.MULTILINE | re.IGNORECASE | re.VERBOSE,
)

FLASHCARD = re.compile(
    r"""
    (?:^|\s)            # Start of line or whitespace
    -\ .*               # Hyphen, space, any characters
    \#card|\[\[card\]\] # Either "#card" or "[[card]]"
    .*                  # Any characters
    """,
    re.MULTILINE | re.IGNORECASE | re.VERBOSE,
)

DYNAMIC_VARIABLE = re.compile(
    r"""
    <%                  # Opening tag
    \s*                 # Optional whitespace
    .*?                 # Any characters (non-greedy)
    \s*                 # Optional whitespace
    %>                  # Closing tag
    """,
    re.IGNORECASE | re.VERBOSE,
)

ANY_LINK = re.compile(
    r"""
    \b                                          # word boundary
    (?:                                       
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
    \b                                          # word boundary
    """,
    re.IGNORECASE | re.VERBOSE,
)
