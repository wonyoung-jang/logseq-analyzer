"""
Compile frequently used regex patterns for Logseq content and configuration.
"""

import logging
import re


class RegexPatterns:
    """
    Class to hold regex patterns for Logseq content and configuration.
    """

    def __init__(self):
        """Initialize the RegexPatterns class."""
        self.content = {}
        self.ext_links = {}
        self.emb_links = {}
        self.dblcurly = {}
        self.advcommand = {}
        self.config = {}
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
                ([^\]]+?)   # Capture group: anything except closing bracket (non-greedy)
                \]\]        # Closing double brackets
                (?=\s+|\])  # Positive lookahead: whitespace or closing bracket
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "tag": re.compile(
                r"""
                \#              # Hash character
                (?!\[\[)        # Negative lookahead: not followed by [[
                (\w+)           # Capture group: word characters
                (?=\s+|\b])     # Positive lookahead: whitespace or word boundary with ]
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
                \.\./assets/    # ../assets/ literal string
                (.*)            # Capture group: anything
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "draw": re.compile(
                r"""
                (?<!\#)              # Negative lookbehind: not preceded by #
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
            "embedded_link": re.compile(
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
                \.\./assets/.*?     # "../assets/" followed by any characters (non-greedy)
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

    def compile_re_config(self):
        """
        Compile and return a dictionary of regex patterns for Logseq configuration.

        Overview of Patterns:
            journal_page_title_pattern: Matches the journal page title format.
            journal_file_name_pattern: Matches the journal file name format.
            feature_enable_journals_pattern: Matches the enable journals feature setting.
            feature_enable_whiteboards_pattern: Matches the enable whiteboards feature setting.
            pages_directory_pattern: Matches the pages directory setting.
            journals_directory_pattern: Matches the journals directory setting.
            whiteboards_directory_pattern: Matches the whiteboards directory setting.
            file_name_format_pattern: Matches the file name format setting.
        """
        self.config = {
            # Pattern to match journal page title format in verbose mode.
            "journal_page_title_format_pattern": re.compile(
                r"""
                :journal/page-title-format  # Literal text for journal page title format.
                \s+                         # One or more whitespace characters.
                "([^"]+)"                   # Capture group for any characters except double quotes.
                """,
                re.VERBOSE,
            ),
            # Pattern to match journal file name format.
            "journal_file_name_format_pattern": re.compile(
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
        logging.info("Compiled regex patterns for configuration analysis.")

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
            "macro": re.compile(
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
                \#\+BEGIN_          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "export": re.compile(
                r"""
                \#\+BEGIN_EXPORT    # "#BEGIN_EXPORT"
                .*?                 # Any characters (non-greedy)
                \#\+END_EXPORT      # "#END_EXPORT"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "export_ascii": re.compile(
                r"""
                \#\+BEGIN_EXPORT        # "#BEGIN_EXPORT ascii"
                \s+?                    # Single space
                ascii                   # "ascii"
                .*?                     # Any characters (non-greedy)
                \#\+END_EXPORT          # "#END_EXPORT"
                .*?                     # Any characters (non-greedy)
                \n                      # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "export_latex": re.compile(
                r"""
                \#\+BEGIN_EXPORT        # "#BEGIN_EXPORT latex"
                \s+?                    # Single space
                latex                   # "latex"                
                .*?                     # Any characters (non-greedy)
                \#\+END_EXPORT          # "#END_EXPORT"
                .*?                     # Any characters (non-greedy)
                \n                      # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "caution": re.compile(
                r"""
                \#\+BEGIN_CAUTION          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_CAUTION      # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "center": re.compile(
                r"""
                \#\+BEGIN_CENTER          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_CENTER      # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "comment": re.compile(
                r"""
                \#\+BEGIN_COMMENT         # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_COMMENT      # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "important": re.compile(
                r"""
                \#\+BEGIN_IMPORTANT          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_IMPORTANT            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "note": re.compile(
                r"""
                \#\+BEGIN_NOTE          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_NOTE            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "pinned": re.compile(
                r"""
                \#\+BEGIN_PINNED          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_PINNED            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "query": re.compile(
                r"""
                \#\+BEGIN_QUERY          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_QUERY            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "quote": re.compile(
                r"""
                \#\+BEGIN_QUOTE          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_QUOTE            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "tip": re.compile(
                r"""
                \#\+BEGIN_TIP          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_TIP            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "verse": re.compile(
                r"""
                \#\+BEGIN_VERSE          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_VERSE            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
            "warning": re.compile(
                r"""
                \#\+BEGIN_WARNING          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_WARNING            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
        }
        logging.info("Compiled regex patterns for content analysis.")
