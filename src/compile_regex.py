"""
Compile frequently used regex patterns for Logseq content and configuration.
"""

from typing import Dict, Pattern
import logging
import re


class RegexPatterns:
    """
    Class to hold regex patterns for Logseq content and configuration.

    Attributes:
        content_patterns (Dict[str, Pattern]): Compiled regex patterns for content.
        config_patterns (Dict[str, Pattern]): Compiled regex patterns for configuration.
    """

    def __init__(self):
        """Initialize the RegexPatterns class."""
        self.content = self.compile_re_content()
        self.config = self.compile_re_config()

    def compile_re_content(self) -> Dict[str, Pattern]:
        """
        Compile and return a dictionary of frequently used regex patterns.

        Returns:
            Dict[str, Pattern]: A dictionary mapping descriptive names to compiled regex patterns.

        Overview of Patterns:
            bullet: Matches bullet points.
            page_reference: Matches internal page references in double brackets.
            tagged_backlink: Matches tagged backlinks.
            tag: Matches hashtags.
            property: Matches property keys.
            property_values: Matches property key-value pairs.
            asset: Matches references to assets.
            draw: Matches references to Excalidraw drawings.
            external_link: Matches markdown external links.
            external_link_internet: Matches external links to websites.
            external_link_alias: Matches aliased external links.
            embedded_link: Matches embedded content links.
            embedded_link_internet: Matches embedded internet content.
            embedded_link_asset: Matches embedded asset references.
            blockquote: Matches blockquote syntax.
            flashcard: Matches flashcard syntax.
            multiline_code_block: Matches code blocks.
            calc_block: Matches calculation blocks.
            multiline_code_lang: Matches code blocks with language specification.
            reference: Matches block references.
            block_reference: Matches UUID block references.
            advanced_command: Matches advanced org-mode commands.
            inline_code: Matches inline code syntax.
            dynamic_variable: Matches dynamic variables.
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
        patterns = {
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
                ([^\]]+)    # Capture group: anything except closing bracket
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
                ([A-Za-z0-9_-]+)    # Capture group: alphanumeric, underscore, or hyphen
                (?=::)              # Positive lookahead: double colon
                """,
                re.MULTILINE | re.IGNORECASE | re.VERBOSE,
            ),
            "property_value": re.compile(
                r"""
                ^                   # Start of line
                (?!\s*-\s)          # Negative lookahead: not a bullet
                \s*?                # Optional whitespace
                ([A-Za-z0-9_-]+)    # Capture group 1: Alphanumeric, underscore, or hyphen
                ::                  # Literal ::
                (.*)                # Capture group 2: Any characters
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
                re.IGNORECASE | re.VERBOSE,
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
                re.IGNORECASE | re.VERBOSE,
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
            "advanced_command": re.compile(
                r"""
                \#\+BEGIN_          # "#BEGIN_"
                .*?                 # Any characters (non-greedy)
                \#\+END_            # "#END_"
                .*?                 # Any characters (non-greedy)
                \n                  # Newline
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
        return patterns

    def compile_re_config(self) -> Dict[str, Pattern]:
        """
        Compile and return a dictionary of regex patterns for Logseq configuration.

        Returns:
            Dict[str, Pattern]: A dictionary mapping descriptive names to compiled regex patterns.

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
        patterns = {
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
        return patterns
