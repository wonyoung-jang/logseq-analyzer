"""
LogseqFile class to represent a Logseq file.
This class contains metadata about the file, including its name, path, creation date, modification date, and content.
"""

from datetime import datetime
import logging
import os
from pathlib import Path
from pprint import pprint
import re
from urllib.parse import unquote

import src.config as config
PROPS = config.BUILT_IN_PROPERTIES


class LogseqFile:
    def __init__(self, file_path: Path):
        # Basic file attributes
        self.id = None
        self.name = None
        self.name_secondary = None
        self.file_path = None
        self.file_path_parent_name = None
        self.file_path_name = None
        self.file_path_suffix = None
        self.file_path_parts = None

        # Date/time attributes
        self.date_created = None
        self.date_modified = None
        self.time_existed = None
        self.time_unmodified = None

        # Content stats
        self.size = None
        self.uri = None
        self.char_count = None
        self.bullet_count = None
        self.bullet_density = None
        
        # Content patterns
        self.content_patterns = None
        
        # Initialize all attributes
        self.initialize_all(file_path)
        
    def __repr__(self):
        return f"LogseqFile({self.name})"
    
    def __str__(self):
        return f"LogseqFile({self.name})"

    def initialize_all(self, file_path: Path):
        stat = file_path.stat()
        self.compile_re_content()
        self.set_basic_file_attributes(file_path)
        self.set_datetime_attributes(file_path, stat)
        self.set_content_stats(file_path, stat)

    def set_basic_file_attributes(self, file_path: Path):
        parent = file_path.parent.name
        name = self.process_filename_key(file_path.stem, parent)
        suffix = file_path.suffix.lower() if file_path.suffix else None

        self.id = name[:2].lower() if len(name) > 1 else f"!{name[0].lower()}"
        self.name = name
        self.name_secondary = f"{name} {parent} + {suffix}".lower()
        self.file_path = str(file_path)
        self.file_path_parent_name = parent.lower()
        self.file_path_name = name.lower()
        self.file_path_suffix = suffix.lower() if suffix else None
        self.file_path_parts = file_path.parts

    def set_datetime_attributes(self, file_path: Path, stat: os.stat_result):
        now = datetime.now().replace(microsecond=0)
        try:
            self.date_created = datetime.fromtimestamp(stat.st_birthtime).replace(microsecond=0)
        except AttributeError:
            self.date_created = datetime.fromtimestamp(stat.st_ctime).replace(microsecond=0)
            logging.warning(f"File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.")
        self.date_modified = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0)
        self.time_existed = now - self.date_created
        self.time_unmodified = now - self.date_modified

    def set_content_stats(self, file_path: Path, stat: os.stat_result):
        self.size = stat.st_size
        self.uri = file_path.as_uri()
        
        content = None
        try:
            content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.warning(f"File not found: {file_path}")
        except Exception as e:
            logging.warning(f"Failed to read file {file_path}: {e}")

        if content:
            self.char_count = len(content)
            bullet_count = len(self.content_patterns["bullet"].findall(content))
            self.bullet_count = bullet_count
            self.bullet_density = self.char_count // bullet_count if bullet_count > 0 else 0

    def compile_re_content(self):
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
            embed: Matches embedded content.
            page_embed: Matches embedded page references.
            block_embed: Matches embedded block references.
            namespace_query: Matches namespace queries.
            cloze: Matches cloze deletions.
            simple_queries: Matches simple query syntax.
            query_functions: Matches query functions.
            advanced_command: Matches advanced org-mode commands.
        """
        logging.info("Compiling regex patterns")
        self.content_patterns = {
            "bullet": re.compile(
                r"""
                (?:^|\s)    # Beginning of line or whitespace
                -           # Literal hyphen
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
                ^               # Start of line
                (?!\s*-\s)      # Negative lookahead: not a bullet
                ([A-Za-z0-9_-]+)# Capture group: alphanumeric, underscore, or hyphen
                (?=::)          # Positive lookahead: double colon
                """,
                re.MULTILINE | re.IGNORECASE | re.VERBOSE,
            ),
            "property_values": re.compile(
                r"""
                ^               # Start of line
                (?!\s*-\s)      # Negative lookahead: not a bullet
                ([A-Za-z0-9_-]+)# Capture group 1: Alphanumeric, underscore, or hyphen
                ::              # Literal ::
                (.*)            # Capture group 2: Any characters
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
            "cloze": re.compile(
                r"""
                \{\{cloze\          # "{{cloze" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "simple_queries": re.compile(
                r"""
                \{\{query\          # "{{query" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "query_functions": re.compile(
                r"""
                \{\{function\       # "{{function" followed by space
                .*?                 # Any characters (non-greedy)
                \}\}                # Closing double braces
                """,
                re.IGNORECASE | re.VERBOSE,
            ),
            "advanced_command": re.compile(
                r"""
                \#\+BEGIN_          # "#BEGIN_"
                .*                  # Any characters
                \#\+END_            # "#END_"
                .*                  # Any characters
                """,
                re.DOTALL | re.IGNORECASE | re.VERBOSE,
            ),
        }

    def transform_date_format(self, cljs_format: str) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.

        Args:
            cljs_format (str): Clojure-style date format.

        Returns:
            str: Python-style date format.
        """

        def replace_token(match):
            token = match.group(0)
            return config.DATETIME_TOKEN_MAP.get(token, token)

        py_format = config.DATETIME_TOKEN_PATTERN.sub(replace_token, cljs_format)
        return py_format

    def process_journal_key(self, key: str) -> str:
        """
        Process the journal key by converting it to a page title format.

        Args:
            key (str): The journal key (filename stem).

        Returns:
            str: Processed journal key as a page title.
        """
        page_title_format = config.JOURNAL_PAGE_TITLE_FORMAT
        file_name_format = config.JOURNAL_FILE_NAME_FORMAT
        py_file_name_format = self.transform_date_format(file_name_format)
        py_page_title_format = self.transform_date_format(page_title_format)

        try:
            date_object = datetime.strptime(key, py_file_name_format)
            page_title = date_object.strftime(py_page_title_format).lower()
            return page_title
        except ValueError:
            logging.warning(f"Could not parse journal key as date: {key}. Returning original key.")
            return key

    def process_filename_key(self, key: str, parent: str) -> str:
        """
        Process the key name by removing the parent name and formatting it.

        For 'journals' parent, it formats the key as 'day-month-year dayOfWeek'.
        For other parents, it unquotes URL-encoded characters and replaces '___' with '/'.

        Args:
            key (str): The key name (filename stem).
            parent (str): The parent directory name.

        Returns:
            str: Processed key name.
        """
        if parent == config.DIR_JOURNALS:
            return self.process_journal_key(key)

        if key.endswith(config.NAMESPACE_FILE_SEP):
            key = key.rstrip(config.NAMESPACE_FILE_SEP)

        return unquote(key).replace(config.NAMESPACE_FILE_SEP, config.NAMESPACE_SEP).lower()
