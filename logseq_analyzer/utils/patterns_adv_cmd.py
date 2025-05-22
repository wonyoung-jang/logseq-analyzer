"""Advanced command patterns for Logseq."""

import re
from collections import defaultdict
from typing import Iterator

from .enums import Criteria

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
    EXPORT_ASCII: Criteria.ADVANCED_COMMANDS_EXPORT_ASCII.value,
    EXPORT_LATEX: Criteria.ADVANCED_COMMANDS_EXPORT_LATEX.value,
    EXPORT: Criteria.ADVANCED_COMMANDS_EXPORT.value,
    CAUTION: Criteria.ADVANCED_COMMANDS_CAUTION.value,
    CENTER: Criteria.ADVANCED_COMMANDS_CENTER.value,
    COMMENT: Criteria.ADVANCED_COMMANDS_COMMENT.value,
    EXAMPLE: Criteria.ADVANCED_COMMANDS_EXAMPLE.value,
    IMPORTANT: Criteria.ADVANCED_COMMANDS_IMPORTANT.value,
    NOTE: Criteria.ADVANCED_COMMANDS_NOTE.value,
    PINNED: Criteria.ADVANCED_COMMANDS_PINNED.value,
    QUERY: Criteria.ADVANCED_COMMANDS_QUERY.value,
    QUOTE: Criteria.ADVANCED_COMMANDS_QUOTE.value,
    TIP: Criteria.ADVANCED_COMMANDS_TIP.value,
    VERSE: Criteria.ADVANCED_COMMANDS_VERSE.value,
    WARNING: Criteria.ADVANCED_COMMANDS_WARNING.value,
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
            output[Criteria.ADVANCED_COMMANDS.value].append(text)

    return output
