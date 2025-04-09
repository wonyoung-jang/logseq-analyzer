"""
Compile frequently used regex patterns for Logseq content.
"""

import logging
import re


class RegexPatterns:
    """
    Class to hold regex patterns for Logseq content.
    """

    def __init__(self):
        """Initialize the RegexPatterns class."""
        self.content = {}
        self.ext_links = {}
        self.emb_links = {}
        self.dblcurly = {}
        self.advcommand = {}
        self.code = {}

    def compile_re_code(self):
        """
        Compile regex patterns for code blocks and related syntax.

        Overview of Patterns:
            multiline_code_block: Matches multi-line code blocks enclosed in triple backticks.
            calc_block: Matches calc blocks enclosed in triple backticks with "calc".
            multiline_code_lang: Matches multi-line code blocks with a specific language defined.
            inline_code_block: Matches inline code blocks enclosed in single backticks.
        """
        self.code = {
            "multiline_code_block": re.compile(
                r"""
                ```                 # Three backticks
                .*?                 # Any characters (non-greedy)
                ```                 # Three backticks
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "calc_block": re.compile(
                r"""
                ```calc             # Three backticks followed by "calc"
                .*?                 # Any characters (non-greedy)
                ```                 # Three backticks
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "multiline_code_lang": re.compile(
                r"""
                ```                 # Three backticks
                \w+                 # One or more word characters
                .*?                 # Any characters (non-greedy)
                ```                 # Three backticks
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "inline_code_block": re.compile(
                r"""
                `                   # One backtick
                \w+                 # One or more word characters
                .*?                 # Any characters (non-greedy)
                `                   # One backtick
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
        }

    def compile_re_content(self):
        """
        Compile and return a dictionary of frequently used regex patterns.

        Overview of Patterns:
            bullet: Matches bullet points.
            page_reference: Matches internal page references in double brackets.
            tagged_backlink: Matches tagged backlinks.
            tag: Matches hashtags.
            property: Matches property keys.
            property_values: Matches property key-value pairs.
            asset: Matches references to assets.
            draw: Matches references to Excalidraw drawings.
            blockquote: Matches blockquote syntax.
            flashcard: Matches flashcard syntax.
            dynamic_variable: Matches dynamic variables.
            reference: Matches block references.
                block_reference: Matches UUID block references.
        """
        self.content = {
            "bullet": re.compile(
                r"""
                ^           # Beginning of line
                \s*         # Optional whitespace
                -           # Literal hyphen
                \s*         # Optional whitespace
                """,
                re.MULTILINE | re.IGNORECASE | re.VERBOSE,
            ),
            "page_reference": re.compile(
                r"""
                (?<!\#)     # Negative lookbehind: not preceded by #
                \[\[        # Opening double brackets
                (.+?)       # Capture group: the page name (non-greedy)
                \]\]        # Closing double brackets
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "tagged_backlink": re.compile(
                r"""
                \#          # Hash character
                \[\[        # Opening double brackets
                [^\]\#]+?   # Anything except closing brackets or hash (non-greedy)
                \]\]        # Closing double brackets
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "tag": re.compile(
                r"""
                \#              # Hash character
                (?!\[\[)        # Negative lookahead: not followed by [[
                [^\]\#\s]+?     # Anything except closing brackets, hash, or whitespace (non-greedy)
                (?=\s|$)        # Followed by whitespace or end of line
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "property": re.compile(
                r"""
                ^                   # Start of line
                (?!\s*-\s)          # Negative lookahead: not a bullet
                \s*?                # Optional whitespace
                ([A-Za-z0-9_-]+?)   # Capture group: alphanumeric, underscore, or hyphen (non-greedy)
                (?=::)              # Positive lookahead: double colon
                """,
                re.MULTILINE | re.IGNORECASE | re.VERBOSE,
            ),
            "property_value": re.compile(
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
            ),
            "asset": re.compile(
                r"""
                assets/         # assets/ literal string
                (.+)            # Capture group: anything except newline (non-greedy)
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "draw": re.compile(
                r"""
                (?<!\#)             # Negative lookbehind: not preceded by #
                \[\[                # Opening double brackets
                draws/(.+?)         # Literal "draws/" followed by capture group
                \.excalidraw        # Literal ".excalidraw"
                \]\]                # Closing double brackets
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "blockquote": re.compile(
                r"""
                (?:^|\s)            # Start of line or whitespace
                -\ >                # Hyphen, space, greater than
                .*                  # Any characters
                """,
                re.MULTILINE | re.IGNORECASE | re.VERBOSE,
            ),
            "flashcard": re.compile(
                r"""
                (?:^|\s)            # Start of line or whitespace
                -\ .*               # Hyphen, space, any characters
                \#card|\[\[card\]\] # Either "#card" or "[[card]]"
                .*                  # Any characters
                """,
                re.MULTILINE | re.IGNORECASE | re.VERBOSE,
            ),
            "reference": re.compile(
                r"""
                (?<!\{\{embed\ )    # Negative lookbehind: not preceded by "{{embed "
                \(\(                # Opening double parentheses
                .*?                 # Any characters (non-greedy)
                \)\)                # Closing double parentheses
                """,
                re.IGNORECASE | re.VERBOSE,
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
                re.IGNORECASE | re.VERBOSE,
            ),
            "dynamic_variable": re.compile(
                r"""
                <%                  # Opening tag
                \s*                 # Optional whitespace
                .*?                 # Any characters (non-greedy)
                \s*                 # Optional whitespace
                %>                  # Closing tag
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
        }
        logging.info("Compiled regex patterns for content analysis.")

    def compile_re_emb_links(self):
        """
        Compile and return a dictionary of regex patterns for embedded links.

        Overview of Patterns:
            embedded_link: Matches embedded content links.
                embedded_link_internet: Matches embedded internet content.
                embedded_link_asset: Matches embedded asset references.
        """
        self.emb_links = {
            "_all": re.compile(
                r"""
                \!                  # Exclamation mark
                \[                  # Opening bracket
                .*?                 # Any characters (non-greedy)
                \]                  # Closing bracket
                \(                  # Opening parenthesis
                .*?                 # Any characters (non-greedy)
                \)                  # Closing parenthesis
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "embedded_link_internet": re.compile(
                r"""
                \!                  # Exclamation mark
                \[                  # Opening bracket
                .*?                 # Any characters (non-greedy)
                \]                  # Closing bracket
                \(                  # Opening parenthesis
                http.*?             # "http" followed by any characters (non-greedy)
                \)                  # Closing parenthesis
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "embedded_link_asset": re.compile(
                r"""
                \!                  # Exclamation mark
                \[                  # Opening bracket
                .*?                 # Any characters (non-greedy)
                \]                  # Closing bracket
                \(                  # Opening parenthesis
                .*?                 # Any characters (non-greedy)
                assets/             # Literal "assets/"
                .*?                 # Any characters (non-greedy)
                \)                  # Closing parenthesis
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
        }

    def compile_re_ext_links(self):
        """
        Compile and return a dictionary of regex patterns for external links.

        Overview of Patterns:
            external_link: Matches markdown-style external links.
                external_link_internet: Matches external links to websites (http/https).
                external_link_alias: Matches aliased external links (e.g., nested links).
        """
        self.ext_links = {
            "_all": re.compile(
                r"""
                (?<!\!)            # Negative lookbehind: not preceded by !
                \[                 # Opening bracket
                .*?                # Any characters (non-greedy)
                \]                 # Closing bracket
                \(                 # Opening parenthesis
                .*?                # Any characters (non-greedy)
                \)                 # Closing parenthesis
                """,
                re.IGNORECASE | re.VERBOSE,
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
                re.IGNORECASE | re.VERBOSE,
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
                re.IGNORECASE | re.VERBOSE,
            ),
        }

    def compile_re_content_double_curly_brackets(self):
        """
        Compile and return a dictionary of frequently used regex patterns.

        Overview of Patterns:
            macro: Matches macro syntax.
                embed: Matches embedded content.
                    page_embed: Matches embedded page references.
                    block_embed: Matches embedded block references.
                namespace_query: Matches namespace queries.
                card: Matches card references.
                cloze: Matches cloze deletions.
                simple_query: Matches simple query syntax.
                query_function: Matches query functions.
                embed_video_url: Matches embedded video URLs.
                embed_twitter_tweet: Matches embedded Twitter tweets.
                embed_youtube_timestamp: Matches embedded YouTube timestamps.
                renderer: Matches renderer syntax.
        """
        self.dblcurly = {
            "_all": re.compile(
                r"""
                \{\{                # Opening double braces
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "embed": re.compile(
                r"""
                \{\{embed\          # "{{embed" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "page_embed": re.compile(
                r"""
                \{\{embed\          # "{{embed" followed by space
                \[\[                # Opening double brackets
                .*?                 # Any characters (non-greedy)
                \]\]                # Closing double brackets
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
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
                re.IGNORECASE | re.VERBOSE,
            ),
            "namespace_query": re.compile(
                r"""
                \{\{namespace\      # "{{namespace" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "card": re.compile(
                r"""
                \{\{cards\          # "{{cards" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "cloze": re.compile(
                r"""
                \{\{cloze\          # "{{cloze" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "simple_query": re.compile(
                r"""
                \{\{query\          # "{{query" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "query_function": re.compile(
                r"""
                \{\{function\       # "{{function" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "embed_video_url": re.compile(
                r"""
                \{\{video\          # "{{video" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "embed_twitter_tweet": re.compile(
                r"""
                \{\{tweet\          # "{{tweet" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "embed_youtube_timestamp": re.compile(
                r"""
                \{\{youtube-timestamp\  # "{{youtube-timestamp" followed by space
                .*?                     # Any characters (non-greedy)
                \}\}                    # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "renderer": re.compile(
                r"""
                \{\{renderer\       # "{{renderer" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
        }
        logging.info("Compiled regex patterns for content analysis.")

    def compile_re_content_advanced_command(self):
        """
        Compile and return a dictionary of frequently used regex patterns.

        Overview of Patterns:
            advanced_command: Matches advanced org-mode commands.
                export
                    ascii
                    latex
                    ...
                caution
                center
                comment
                important
                note
                pinned
                query
                quote
                tip
                verse
                warning
        """
        self.advcommand = {
            "_all": re.compile(
                r"""
                \#\+BEGIN_          # "#+BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_            # "#+END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "export": re.compile(
                r"""
                \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT"
                .*?                 # Any characters (non-greedy)
                \#\+END_EXPORT      # "#+END_EXPORT"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "export_ascii": re.compile(
                r"""
                \#\+BEGIN_EXPORT        # "#+BEGIN_EXPORT ascii"
                \s+?                    # Single space
                ascii                   # "ascii"
                .*?                     # Any characters (non-greedy)
                \#\+END_EXPORT          # "#+END_EXPORT"
                .*?                     # Any characters (non-greedy)
                \n                      # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "export_latex": re.compile(
                r"""
                \#\+BEGIN_EXPORT        # "#+BEGIN_EXPORT latex"
                \s+?                    # Single space
                latex                   # "latex"
                .*?                     # Any characters (non-greedy)
                \#\+END_EXPORT          # "#+END_EXPORT"
                .*?                     # Any characters (non-greedy)
                \n                      # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "caution": re.compile(
                r"""
                \#\+BEGIN_CAUTION   # "#+BEGIN_CAUTION"
                .*?                 # Any characters (non-greedy)
                \#\+END_CAUTION     # "#+END_CAUTION"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "center": re.compile(
                r"""
                \#\+BEGIN_CENTER    # "#+BEGIN_CENTER"
                .*?                 # Any characters (non-greedy)
                \#\+END_CENTER      # "#+END_CENTER"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "comment": re.compile(
                r"""
                \#\+BEGIN_COMMENT   # "#+BEGIN_COMMENT"
                .*?                 # Any characters (non-greedy)
                \#\+END_COMMENT     # "#+END_COMMENT"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "example": re.compile(
                r"""
                \#\+BEGIN_EXAMPLE   # "#+BEGIN_EXAMPLE"
                .*?                 # Any characters (non-greedy)
                \#\+END_EXAMPLE     # "#+END_EXAMPLE"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "important": re.compile(
                r"""
                \#\+BEGIN_IMPORTANT # "#+BEGIN_IMPORTANT"
                .*?                 # Any characters (non-greedy)
                \#\+END_IMPORTANT   # "#+END_IMPORTANT"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "note": re.compile(
                r"""
                \#\+BEGIN_NOTE      # "#+BEGIN_NOTE"
                .*?                 # Any characters (non-greedy)
                \#\+END_NOTE        # "#+END_NOTE"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "pinned": re.compile(
                r"""
                \#\+BEGIN_PINNED    # "#+BEGIN_PINNED"
                .*?                 # Any characters (non-greedy)
                \#\+END_PINNED      # "#+END_PINNED"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "query": re.compile(
                r"""
                \#\+BEGIN_QUERY     # "#+BEGIN_QUERY"
                .*?                 # Any characters (non-greedy)
                \#\+END_QUERY       # "#+END_QUERY"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "quote": re.compile(
                r"""
                \#\+BEGIN_QUOTE     # "#+BEGIN_QUOTE"
                .*?                 # Any characters (non-greedy)
                \#\+END_QUOTE       # "#+END_QUOTE"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "tip": re.compile(
                r"""
                \#\+BEGIN_TIP       # "#+BEGIN_TIP"
                .*?                 # Any characters (non-greedy)
                \#\+END_TIP         # "#+END_TIP"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "verse": re.compile(
                r"""
                \#\+BEGIN_VERSE     # "#+BEGIN_VERSE"
                .*?                 # Any characters (non-greedy)
                \#\+END_VERSE       # "#+END_VERSE"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "warning": re.compile(
                r"""
                \#\+BEGIN_WARNING   # "#+BEGIN_WARNING"
                .*?                 # Any characters (non-greedy)
                \#\+END_WARNING     # "#+END_WARNING"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
        }
        logging.info("Compiled regex patterns for content analysis.")
