"""Advanced command patterns for Logseq."""

import re

from ..utils.enums import Criteria

ALL = re.compile(
    r"""
    \#\+BEGIN_          # "#+BEGIN_"
    .*?                 # Any characters (non-greedy)
    \#\+END_            # "#+END_"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

EXPORT = re.compile(
    r"""
    \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT"
    .*?                 # Any characters (non-greedy)
    \#\+END_EXPORT      # "#+END_EXPORT"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

EXPORT_ASCII = re.compile(
    r"""
    \#\+BEGIN_EXPORT        # "#+BEGIN_EXPORT ascii"
    \s{1}                   # Single space
    ascii                   # "ascii"
    .*?                     # Any characters (non-greedy)
    \#\+END_EXPORT          # "#+END_EXPORT"
    .*?                     # Any characters (non-greedy)
    (?:\n|$)                # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

EXPORT_LATEX = re.compile(
    r"""
    \#\+BEGIN_EXPORT        # "#+BEGIN_EXPORT latex"
    \s{1}                   # Single space
    latex                   # "latex"
    .*?                     # Any characters (non-greedy)
    \#\+END_EXPORT          # "#+END_EXPORT"
    .*?                     # Any characters (non-greedy)
    (?:\n|$)                # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

CAUTION = re.compile(
    r"""
    \#\+BEGIN_CAUTION   # "#+BEGIN_CAUTION"
    .*?                 # Any characters (non-greedy)
    \#\+END_CAUTION     # "#+END_CAUTION"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

CENTER = re.compile(
    r"""
    \#\+BEGIN_CENTER    # "#+BEGIN_CENTER"
    .*?                 # Any characters (non-greedy)
    \#\+END_CENTER      # "#+END_CENTER"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

COMMENT = re.compile(
    r"""
    \#\+BEGIN_COMMENT   # "#+BEGIN_COMMENT"
    .*?                 # Any characters (non-greedy)
    \#\+END_COMMENT     # "#+END_COMMENT"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

EXAMPLE = re.compile(
    r"""
    \#\+BEGIN_EXAMPLE   # "#+BEGIN_EXAMPLE"
    .*?                 # Any characters (non-greedy)
    \#\+END_EXAMPLE     # "#+END_EXAMPLE"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

IMPORTANT = re.compile(
    r"""
    \#\+BEGIN_IMPORTANT # "#+BEGIN_IMPORTANT"
    .*?                 # Any characters (non-greedy)
    \#\+END_IMPORTANT   # "#+END_IMPORTANT"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

NOTE = re.compile(
    r"""
    \#\+BEGIN_NOTE      # "#+BEGIN_NOTE"
    .*?                 # Any characters (non-greedy)
    \#\+END_NOTE        # "#+END_NOTE"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

PINNED = re.compile(
    r"""
    \#\+BEGIN_PINNED    # "#+BEGIN_PINNED"
    .*?                 # Any characters (non-greedy)
    \#\+END_PINNED      # "#+END_PINNED"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

QUERY = re.compile(
    r"""
    \#\+BEGIN_QUERY     # "#+BEGIN_QUERY"
    .*?                 # Any characters (non-greedy)
    \#\+END_QUERY       # "#+END_QUERY"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

QUOTE = re.compile(
    r"""
    \#\+BEGIN_QUOTE     # "#+BEGIN_QUOTE"
    .*?                 # Any characters (non-greedy)
    \#\+END_QUOTE       # "#+END_QUOTE"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

TIP = re.compile(
    r"""
    \#\+BEGIN_TIP       # "#+BEGIN_TIP"
    .*?                 # Any characters (non-greedy)
    \#\+END_TIP         # "#+END_TIP"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

VERSE = re.compile(
    r"""
    \#\+BEGIN_VERSE     # "#+BEGIN_VERSE"
    .*?                 # Any characters (non-greedy)
    \#\+END_VERSE       # "#+END_VERSE"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

WARNING = re.compile(
    r"""
    \#\+BEGIN_WARNING   # "#+BEGIN_WARNING"
    .*?                 # Any characters (non-greedy)
    \#\+END_WARNING     # "#+END_WARNING"
    .*?                 # Any characters (non-greedy)
    (?:\n|$)            # Newline or end-of-file
    """,
    re.DOTALL | re.IGNORECASE | re.VERBOSE,
)

PATTERN_MAP = {
    EXPORT_ASCII: Criteria.ADV_CMD_EXPORT_ASCII,
    EXPORT_LATEX: Criteria.ADV_CMD_EXPORT_LATEX,
    EXPORT: Criteria.ADV_CMD_EXPORT,
    CAUTION: Criteria.ADV_CMD_CAUTION,
    CENTER: Criteria.ADV_CMD_CENTER,
    COMMENT: Criteria.ADV_CMD_COMMENT,
    EXAMPLE: Criteria.ADV_CMD_EXAMPLE,
    IMPORTANT: Criteria.ADV_CMD_IMPORTANT,
    NOTE: Criteria.ADV_CMD_NOTE,
    PINNED: Criteria.ADV_CMD_PINNED,
    QUERY: Criteria.ADV_CMD_QUERY,
    QUOTE: Criteria.ADV_CMD_QUOTE,
    TIP: Criteria.ADV_CMD_TIP,
    VERSE: Criteria.ADV_CMD_VERSE,
    WARNING: Criteria.ADV_CMD_WARNING,
}

FALLBACK = Criteria.ADV_CMD
