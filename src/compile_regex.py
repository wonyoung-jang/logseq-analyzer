import logging
import re
from typing import Dict, Pattern


def compile_re_content() -> Dict[str, Pattern]:
    """
    Compile and return a dictionary of frequently used regex patterns.

    Returns:
        Dict[str, Pattern]: A dictionary mapping descriptive names to compiled regex patterns.
    """
    logging.info("Compiling regex patterns")
    patterns = {
        "bullet": re.compile(
            r"""
            (?:^|\s)    # Beginning of line or whitespace
            -           # Literal hyphen
            """,
            re.M | re.I | re.X,
        ),
        "page_reference": re.compile(
            r"""
            (?<!\#)      # Negative lookbehind: not preceded by #
            \[\[        # Opening double brackets
            (.+?)       # Capture group: the page name (non-greedy)
            \]\]        # Closing double brackets
            """,
            re.I | re.X,
        ),
        "tagged_backlink": re.compile(
            r"""
            \#          # Hash character
            \[\[        # Opening double brackets
            ([^\]]+)    # Capture group: anything except closing bracket
            \]\]        # Closing double brackets
            (?=\s+|\])  # Positive lookahead: whitespace or closing bracket
            """,
            re.I | re.X,
        ),
        "tag": re.compile(
            r"""
            \#              # Hash character
            (?!\[\[)        # Negative lookahead: not followed by [[
            (\w+)           # Capture group: word characters
            (?=\s+|\b])     # Positive lookahead: whitespace or word boundary with ]
            """,
            re.I | re.X,
        ),
        "property": re.compile(
            r"""
            ^               # Start of line
            (?!\s*-\s)      # Negative lookahead: not a bullet
            ([A-Za-z0-9_-]+)# Capture group: alphanumeric, underscore, or hyphen
            (?=::)          # Positive lookahead: double colon
            """,
            re.M | re.I | re.X,
        ),
        "asset": re.compile(
            r"""
            \.\./assets/    # ../assets/ literal string
            (.*)            # Capture group: anything
            """,
            re.I | re.X,
        ),
        "draw": re.compile(
            r"""
            (?<!\#)              # Negative lookbehind: not preceded by #
            \[\[                # Opening double brackets
            draws/(.+?)         # Literal "draws/" followed by capture group
            \.excalidraw        # Literal ".excalidraw"
            \]\]                # Closing double brackets
            """,
            re.I | re.X,
        ),
        "external_link": re.compile(
            r"""
            (?<!\!)            # Negative lookbehind: not preceded by !
            \[                 # Opening bracket
            .*?                # Any characters (non-greedy)
            \]                 # Closing bracket
            \(                 # Opening parenthesis
            .*?                # Any characters (non-greedy)
            \)                 # Closing parenthesis
            """,
            re.I | re.X,
        ),
        "external_link_internet": re.compile(
            r"""
            (?<!\!)            # Negative lookbehind: not preceded by !
            \[                 # Opening bracket
            .*?                # Any characters (non-greedy)
            \]                 # Closing bracket
            \(                 # Opening parenthesis
            http.*?            # "http" followed by any characters (non-greedy)
            \)                 # Closing parenthesis
            """,
            re.I | re.X,
        ),
        "external_link_alias": re.compile(
            r"""
            (?<!\!)                # Negative lookbehind: not preceded by !
            \[                     # Opening bracket
            .*?                    # Any characters (non-greedy)
            \]                     # Closing bracket
            \(                     # Opening parenthesis
            [\[\[|\(\(]            # Either [[ or ((
            .*?                    # Any characters (non-greedy)
            [\]\]|\)\)]            # Either ]] or ))
            .*?                    # Any characters (non-greedy)
            \)                     # Closing parenthesis
            """,
            re.I | re.X,
        ),
        "embedded_link": re.compile(
            r"""
            \!                  # Exclamation mark
            \[                  # Opening bracket
            .*?                 # Any characters (non-greedy)
            \]                  # Closing bracket
            \(                  # Opening parenthesis
            .*                  # Any characters
            \)                  # Closing parenthesis
            """,
            re.I | re.X,
        ),
        "embedded_link_internet": re.compile(
            r"""
            \!                  # Exclamation mark
            \[                  # Opening bracket
            .*?                 # Any characters (non-greedy)
            \]                  # Closing bracket
            \(                  # Opening parenthesis
            http.*              # "http" followed by any characters
            \)                  # Closing parenthesis
            """,
            re.I | re.X,
        ),
        "embedded_link_asset": re.compile(
            r"""
            \!                  # Exclamation mark
            \[                  # Opening bracket
            .*?                 # Any characters (non-greedy)
            \]                  # Closing bracket
            \(                  # Opening parenthesis
            \.\./assets/.*      # "../assets/" followed by any characters
            \)                  # Closing parenthesis
            """,
            re.I | re.X,
        ),
        "blockquote": re.compile(
            r"""
            (?:^|\s)            # Start of line or whitespace
            -\ >                # Hyphen, space, greater than
            .*                  # Any characters
            """,
            re.M | re.I | re.X,
        ),
        "flashcard": re.compile(
            r"""
            (?:^|\s)            # Start of line or whitespace
            -\ .*               # Hyphen, space, any characters
            \#card|\[\[card\]\] # Either "#card" or "[[card]]"
            .*                  # Any characters
            """,
            re.M | re.I | re.X,
        ),
        "multiline_code_block": re.compile(
            r"""
            ```                 # Three backticks
            .*?                 # Any characters (non-greedy)
            ```                 # Three backticks
            """,
            re.S | re.I | re.X,
        ),
        "calc_block": re.compile(
            r"""
            ```calc             # Three backticks followed by "calc"
            .*?                 # Any characters (non-greedy)
            ```                 # Three backticks
            """,
            re.S | re.I | re.X,
        ),
        "multiline_code_lang": re.compile(
            r"""
            ```                 # Three backticks
            \w+                 # One or more word characters
            .*?                 # Any characters (non-greedy)
            ```                 # Three backticks
            """,
            re.S | re.I | re.X,
        ),
        "reference": re.compile(
            r"""
            (?<!\{\{embed\ )    # Negative lookbehind: not preceded by "{{embed "
            \(\(                # Opening double parentheses
            .*?                 # Any characters (non-greedy)
            \)\)                # Closing double parentheses
            """,
            re.I | re.X,
        ),
        "block_reference": re.compile(
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
            re.I | re.X,
        ),
        "embed": re.compile(
            r"""
            \{\{embed\          # "{{embed" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "page_embed": re.compile(
            r"""
            \{\{embed\          # "{{embed" followed by space
            \[\[                # Opening double brackets
            .*?                 # Any characters (non-greedy)
            \]\]                # Closing double brackets
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "block_embed": re.compile(
            r"""
            \{\{embed\          # "{{embed" followed by space
            \(\(                # Opening double parentheses
            [0-9a-f]{8}-        # 8 hex digits followed by hyphen
            [0-9a-f]{4}-        # 4 hex digits followed by hyphen
            [0-9a-f]{4}-        # 4 hex digits followed by hyphen
            [0-9a-f]{4}-        # 4 hex digits followed by hyphen
            [0-9a-f]{12}        # 12 hex digits
            \)\)                # Closing double parentheses
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "namespace_query": re.compile(
            r"""
            \{\{namespace\      # "{{namespace" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "cloze": re.compile(
            r"""
            \{\{cloze\          # "{{cloze" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "simple_queries": re.compile(
            r"""
            \{\{query\          # "{{query" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "query_functions": re.compile(
            r"""
            \{\{function\       # "{{function" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.I | re.X,
        ),
        "advanced_command": re.compile(
            r"""
            \#\+BEGIN_          # "#BEGIN_"
            .*                  # Any characters
            \#\+END_            # "#END_"
            .*                  # Any characters
            """,
            re.S | re.I | re.X,
        ),
    }
    return patterns


def compile_re_config() -> Dict[str, Pattern]:
    patterns = {
        # Pattern to match journal page title format in verbose mode.
        "journal_page_title_pattern": re.compile(
            r"""
            :journal/page-title-format   # Literal text for journal page title format.
            \s+                          # One or more whitespace characters.
            "([^"]+)"                    # Capture group for any characters except double quotes.
            """,
            re.VERBOSE,
        ),
        # Pattern to match journal file name format.
        "journal_file_name_pattern": re.compile(
            r"""
            :journal/file-name-format    # Literal text for journal file name format.
            \s+                          # One or more whitespace characters.
            "([^"]+)"                    # Capture group for file name format.
            """,
            re.VERBOSE,
        ),
        # Pattern to match whether journals feature is enabled (true or false).
        "feature_enable_journals_pattern": re.compile(
            r"""
            :feature/enable-journals\?   # Literal text for enabling journals feature.
            \s+                          # One or more whitespace characters.
            (true|false)                 # Capture group for 'true' or 'false'.
            """,
            re.VERBOSE,
        ),
        # Pattern to match whether whiteboards feature is enabled (true or false).
        "feature_enable_whiteboards_pattern": re.compile(
            r"""
            :feature/enable-whiteboards\?  # Literal text for enabling whiteboards feature.
            \s+                           # One or more whitespace characters.
            (true|false)                  # Capture group for 'true' or 'false'.
            """,
            re.VERBOSE,
        ),
        # Pattern to match the pages directory.
        "pages_directory_pattern": re.compile(
            r"""
            :pages-directory             # Literal text for pages directory.
            \s+                         # One or more whitespace characters.
            "([^"]+)"                   # Capture group for the directory path.
            """,
            re.VERBOSE,
        ),
        # Pattern to match the journals directory.
        "journals_directory_pattern": re.compile(
            r"""
            :journals-directory          # Literal text for journals directory.
            \s+                         # One or more whitespace characters.
            "([^"]+)"                   # Capture group for the directory path.
            """,
            re.VERBOSE,
        ),
        # Pattern to match the whiteboards directory.
        "whiteboards_directory_pattern": re.compile(
            r"""
            :whiteboards-directory       # Literal text for whiteboards directory.
            \s+                         # One or more whitespace characters.
            "([^"]+)"                   # Capture group for the directory path.
            """,
            re.VERBOSE,
        ),
        # Pattern to match file name format.
        "file_name_format_pattern": re.compile(
            r"""
            :file/name-format            # Literal text for file name format.
            \s+                          # One or more whitespace characters.
            (.+)                         # Capture group for the file name format.
            """,
            re.VERBOSE,
        ),
    }
    return patterns


def compile_re_date(token_map):
    return re.compile("|".join(re.escape(k) for k in sorted(token_map, key=len, reverse=True)))
