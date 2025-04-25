"""
Compile frequently used regex patterns for Logseq content.
"""

from collections import defaultdict
from dataclasses import dataclass
import logging
import re
from typing import Dict, List

from .enums import Criteria

from .helpers import singleton


@singleton
@dataclass
class ContentPatterns:
    """
    Class to hold regex patterns for content in Logseq files.
    """

    bullet = None
    page_reference = None
    tagged_backlink = None
    tag = None
    property = None
    property_value = None
    asset = None
    draw = None
    blockquote = None
    flashcard = None
    dynamic_variable = None
    any_link = None

    def __post_init__(self):
        """
        Compile and return a dictionary of frequently used regex patterns.

        Attributes:
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
            any_link: Matches any link format.
        """
        self.bullet = re.compile(
            r"""
            ^           # Beginning of line
            \s*         # Optional whitespace
            -           # Literal hyphen
            \s*         # Optional whitespace
            """,
            re.MULTILINE | re.IGNORECASE | re.VERBOSE,
        )
        self.page_reference = re.compile(
            r"""
            (?<!\#)     # Negative lookbehind: not preceded by #
            \[\[        # Opening double brackets
            (.+?)       # Capture group: the page name (non-greedy)
            \]\]        # Closing double brackets
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.tagged_backlink = re.compile(
            r"""
            \#          # Hash character
            \[\[        # Opening double brackets
            ([^\]\#]+?) # Anything except closing brackets or hash (non-greedy)
            \]\]        # Closing double brackets
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.tag = re.compile(
            r"""
            \#              # Hash character
            (?!\[\[)        # Negative lookahead: not followed by [[
            ([^\]\#\s]+?)   # Anything except closing brackets, hash, or whitespace (non-greedy)
            (?=\s|$)        # Followed by whitespace or end of line
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.property = re.compile(
            r"""
            ^                   # Start of line
            (?!\s*-\s)          # Negative lookahead: not a bullet
            \s*?                # Optional whitespace
            ([A-Za-z0-9_-]+?)   # Capture group: alphanumeric, underscore, or hyphen (non-greedy)
            (?=::)              # Positive lookahead: double colon
            """,
            re.MULTILINE | re.IGNORECASE | re.VERBOSE,
        )
        self.property_value = re.compile(
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
        self.asset = re.compile(
            r"""
            assets/         # assets/ literal string
            (.+)            # Capture group: anything except newline (non-greedy)
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.draw = re.compile(
            r"""
            (?<!\#)             # Negative lookbehind: not preceded by #
            \[\[                # Opening double brackets
            draws/(.+?)         # Literal "draws/" followed by capture group
            \.excalidraw        # Literal ".excalidraw"
            \]\]                # Closing double brackets
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.blockquote = re.compile(
            r"""
            (?:^|\s)            # Start of line or whitespace
            -\ >                # Hyphen, space, greater than
            .*                  # Any characters
            """,
            re.MULTILINE | re.IGNORECASE | re.VERBOSE,
        )
        self.flashcard = re.compile(
            r"""
            (?:^|\s)            # Start of line or whitespace
            -\ .*               # Hyphen, space, any characters
            \#card|\[\[card\]\] # Either "#card" or "[[card]]"
            .*                  # Any characters
            """,
            re.MULTILINE | re.IGNORECASE | re.VERBOSE,
        )
        self.dynamic_variable = re.compile(
            r"""
            <%                  # Opening tag
            \s*                 # Optional whitespace
            .*?                 # Any characters (non-greedy)
            \s*                 # Optional whitespace
            %>                  # Closing tag
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.any_link = re.compile(
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
        logging.info("Compiled ContentPatterns")


@singleton
@dataclass
class DoubleCurlyBracketsPatterns:
    """
    Class to hold regex patterns for double curly brackets in Logseq content.
    """

    all = None
    embed = None
    page_embed = None
    block_embed = None
    namespace_query = None
    card = None
    cloze = None
    simple_query = None
    query_function = None
    embed_video_url = None
    embed_twitter_tweet = None
    embed_youtube_timestamp = None
    renderer = None

    def __post_init__(self):
        """
        Compile and return a dictionary of regex patterns for double curly brackets.

        Attributes:
            all: Matches macro syntax.
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
        self.all = re.compile(
            r"""
            \{\{                # Opening double braces
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.embed = re.compile(
            r"""
            \{\{embed\          # "{{embed" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.page_embed = re.compile(
            r"""
            \{\{embed\          # "{{embed" followed by space
            \[\[                # Opening double brackets
            .*?                 # Any characters (non-greedy)
            \]\]                # Closing double brackets
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.block_embed = re.compile(
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
        )
        self.namespace_query = re.compile(
            r"""
            \{\{namespace\      # "{{namespace" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.card = re.compile(
            r"""
            \{\{cards\          # "{{cards" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.cloze = re.compile(
            r"""
            \{\{cloze\          # "{{cloze" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.simple_query = re.compile(
            r"""
            \{\{query\          # "{{query" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.query_function = re.compile(
            r"""
            \{\{function\       # "{{function" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.embed_video_url = re.compile(
            r"""
            \{\{video\          # "{{video" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.embed_twitter_tweet = re.compile(
            r"""
            \{\{tweet\          # "{{tweet" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.embed_youtube_timestamp = re.compile(
            r"""
            \{\{youtube-timestamp\  # "{{youtube-timestamp" followed by space
            .*?                     # Any characters (non-greedy)
            \}\}                    # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.renderer = re.compile(
            r"""
            \{\{renderer\       # "{{renderer" followed by space
            .*?                 # Any characters (non-greedy)
            \}\}                # Closing double braces
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        logging.info("Compiled DoubleCurlyBracketsPatterns")

    def process(self, results: List[str]) -> Dict[str, List[str]]:
        """
        Process double curly braces and extract relevant data.

        Args:
            results (List[str]): List of double curly brace strings.

        Returns:
            Dict[str, List[str]]: Dictionary categorizing double curly brace data.
        """
        if not results:
            return {}

        double_curly_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if self.embed.search(result):
                double_curly_family[Criteria.EMBEDS.value].append(result)
                results.pop()
                if self.page_embed.search(result):
                    double_curly_family[Criteria.PAGE_EMBEDS.value].append(result)
                    double_curly_family[Criteria.EMBEDS.value].remove(result)
                    continue
                if self.block_embed.search(result):
                    double_curly_family[Criteria.BLOCK_EMBEDS.value].append(result)
                    double_curly_family[Criteria.EMBEDS.value].remove(result)
                    continue
            if self.namespace_query.search(result):
                double_curly_family[Criteria.NAMESPACE_QUERIES.value].append(result)
                results.pop()
                continue
            if self.card.search(result):
                double_curly_family[Criteria.CARDS.value].append(result)
                results.pop()
                continue
            if self.cloze.search(result):
                double_curly_family[Criteria.CLOZES.value].append(result)
                results.pop()
                continue
            if self.simple_query.search(result):
                double_curly_family[Criteria.SIMPLE_QUERIES.value].append(result)
                results.pop()
                continue
            if self.query_function.search(result):
                double_curly_family[Criteria.QUERY_FUNCTIONS.value].append(result)
                results.pop()
                continue
            if self.embed_video_url.search(result):
                double_curly_family[Criteria.EMBED_VIDEO_URLS.value].append(result)
                results.pop()
                continue
            if self.embed_twitter_tweet.search(result):
                double_curly_family[Criteria.EMBED_TWITTER_TWEETS.value].append(result)
                results.pop()
                continue
            if self.embed_youtube_timestamp.search(result):
                double_curly_family[Criteria.EMBED_YOUTUBE_TIMESTAMPS.value].append(result)
                results.pop()
                continue
            if self.renderer.search(result):
                double_curly_family[Criteria.RENDERERS.value].append(result)
                results.pop()
                continue

        double_curly_family[Criteria.MACROS.value] = results

        return double_curly_family


@singleton
@dataclass
class AdvancedCommandPatterns:
    """
    Class to hold regex patterns for advanced commands in Logseq content.
    """

    all = None
    export = None
    export_ascii = None
    export_latex = None
    caution = None
    center = None
    comment = None
    example = None
    important = None
    note = None
    pinned = None
    query = None
    quote = None
    tip = None
    verse = None
    warning = None

    def __post_init__(self):
        """
        Compile and return a dictionary of frequently used regex patterns.

        Attributes:
            all: Matches advanced org-mode commands.
            export: Matches export blocks.
            export_ascii: Matches ASCII export blocks.
            export_latex: Matches LaTeX export blocks.
            caution: Matches caution blocks.
            center: Matches center blocks.
            comment: Matches comment blocks.
            example: Matches example blocks.
            important: Matches important blocks.
            note: Matches note blocks.
            pinned: Matches pinned blocks.
            query: Matches query blocks.
            quote: Matches quote blocks.
            tip: Matches tip blocks.
            verse: Matches verse blocks.
            warning: Matches warning blocks.
        """
        self.all = re.compile(
            r"""
            \#\+BEGIN_          # "#+BEGIN_"
            .*?                 # Any characters (non-greedy)
            \#\+END_            # "#+END_"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.export = re.compile(
            r"""
            \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT"
            .*?                 # Any characters (non-greedy)
            \#\+END_EXPORT      # "#+END_EXPORT"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.export_ascii = re.compile(
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
        self.export_latex = re.compile(
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
        self.caution = re.compile(
            r"""
            \#\+BEGIN_CAUTION   # "#+BEGIN_CAUTION"
            .*?                 # Any characters (non-greedy)
            \#\+END_CAUTION     # "#+END_CAUTION"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.center = re.compile(
            r"""
            \#\+BEGIN_CENTER    # "#+BEGIN_CENTER"
            .*?                 # Any characters (non-greedy)
            \#\+END_CENTER      # "#+END_CENTER"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.comment = re.compile(
            r"""
            \#\+BEGIN_COMMENT   # "#+BEGIN_COMMENT"
            .*?                 # Any characters (non-greedy)
            \#\+END_COMMENT     # "#+END_COMMENT"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.example = re.compile(
            r"""
            \#\+BEGIN_EXAMPLE   # "#+BEGIN_EXAMPLE"
            .*?                 # Any characters (non-greedy)
            \#\+END_EXAMPLE     # "#+END_EXAMPLE"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.important = re.compile(
            r"""
            \#\+BEGIN_IMPORTANT # "#+BEGIN_IMPORTANT"
            .*?                 # Any characters (non-greedy)
            \#\+END_IMPORTANT   # "#+END_IMPORTANT"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.note = re.compile(
            r"""
            \#\+BEGIN_NOTE      # "#+BEGIN_NOTE"
            .*?                 # Any characters (non-greedy)
            \#\+END_NOTE        # "#+END_NOTE"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.pinned = re.compile(
            r"""
            \#\+BEGIN_PINNED    # "#+BEGIN_PINNED"
            .*?                 # Any characters (non-greedy)
            \#\+END_PINNED      # "#+END_PINNED"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.query = re.compile(
            r"""
            \#\+BEGIN_QUERY     # "#+BEGIN_QUERY"
            .*?                 # Any characters (non-greedy)
            \#\+END_QUERY       # "#+END_QUERY"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.quote = re.compile(
            r"""
            \#\+BEGIN_QUOTE     # "#+BEGIN_QUOTE"
            .*?                 # Any characters (non-greedy)
            \#\+END_QUOTE       # "#+END_QUOTE"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.tip = re.compile(
            r"""
            \#\+BEGIN_TIP       # "#+BEGIN_TIP"
            .*?                 # Any characters (non-greedy)
            \#\+END_TIP         # "#+END_TIP"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.verse = re.compile(
            r"""
            \#\+BEGIN_VERSE     # "#+BEGIN_VERSE"
            .*?                 # Any characters (non-greedy)
            \#\+END_VERSE       # "#+END_VERSE"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.warning = re.compile(
            r"""
            \#\+BEGIN_WARNING   # "#+BEGIN_WARNING"
            .*?                 # Any characters (non-greedy)
            \#\+END_WARNING     # "#+END_WARNING"
            .*?                 # Any characters (non-greedy)
            (?:\n|$)            # Newline or end-of-file
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        logging.info("Compiled AdvancedCommandPatterns")

    def process(self, results: List[str]) -> Dict[str, List[str]]:
        """
        Process advanced commands and extract relevant data.

        Args:
            results (List[str]): List of advanced command strings.

        Returns:
            Dict[str, List[str]]: Dictionary categorizing advanced commands.
        """
        if not results:
            return {}

        advanced_command_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if self.export.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].append(result)
                results.pop()
                if self.export_ascii.search(result):
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT_ASCII.value].append(result)
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].pop()
                    continue
                if self.export_latex.search(result):
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT_LATEX.value].append(result)
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].pop()
                    continue
            if self.caution.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_CAUTION.value].append(result)
                results.pop()
                continue
            if self.center.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_CENTER.value].append(result)
                results.pop()
                continue
            if self.comment.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_COMMENT.value].append(result)
                results.pop()
                continue
            if self.example.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_EXAMPLE.value].append(result)
                results.pop()
                continue
            if self.important.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_IMPORTANT.value].append(result)
                results.pop()
                continue
            if self.note.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_NOTE.value].append(result)
                results.pop()
                continue
            if self.pinned.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_PINNED.value].append(result)
                results.pop()
                continue
            if self.query.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_QUERY.value].append(result)
                results.pop()
                continue
            if self.quote.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_QUOTE.value].append(result)
                results.pop()
                continue
            if self.tip.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_TIP.value].append(result)
                results.pop()
                continue
            if self.verse.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_VERSE.value].append(result)
                results.pop()
                continue
            if self.warning.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_WARNING.value].append(result)
                results.pop()
                continue

        advanced_command_family[Criteria.ADVANCED_COMMANDS.value] = results

        return advanced_command_family


@singleton
@dataclass
class CodePatterns:
    """
    Class to hold regex patterns for code blocks in Logseq content.
    """

    all = None
    multiline_code_lang = None
    calc_block = None
    inline_code_block = None

    def __post_init__(self):
        """
        Compile and return a dictionary of regex patterns for code blocks.

        Attributes:
            all: Matches all code blocks.
            multiline_code_lang: Matches multiline code blocks with a specified language.
            calc_block: Matches calculation blocks.
            inline_code_block: Matches inline code blocks.
        """
        self.all = re.compile(
            r"""
            ```                 # Three backticks
            .*?                 # Any characters (non-greedy)
            ```                 # Three backticks
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.multiline_code_lang = re.compile(
            r"""
            ```                 # Three backticks
            \w+                 # One or more word characters
            .*?                 # Any characters (non-greedy)
            ```                 # Three backticks
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.calc_block = re.compile(
            r"""
            ```calc             # Three backticks followed by "calc"
            .*?                 # Any characters (non-greedy)
            ```                 # Three backticks
            """,
            re.DOTALL | re.IGNORECASE | re.VERBOSE,
        )
        self.inline_code_block = re.compile(
            r"""
            `                   # One backtick
            .+?                 # One or more characters (non-greedy)
            `                   # One backtick
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        logging.info("Compiled CodePatterns")

    def process(self, results: List[str]) -> Dict[str, List[str]]:
        """
        Process code blocks and categorize them.

        Args:
            results (List[str]): List of code block strings.

        Returns:
            Dict[str, List[str]]: Dictionary categorizing code blocks.
        """
        if not results:
            return {}

        code_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if self.calc_block.search(result):
                code_family[Criteria.CALC_BLOCKS.value].append(result)
                results.pop()
                continue
            if self.multiline_code_lang.search(result):
                code_family[Criteria.MULTILINE_CODE_LANGS.value].append(result)
                results.pop()
                continue

        code_family[Criteria.MULTILINE_CODE_BLOCKS.value] = results

        return code_family


@singleton
@dataclass
class DoubleParenthesesPatterns:
    """
    Class to hold regex patterns for double parentheses in Logseq content.
    """

    all = None
    block_reference = None

    def __post_init__(self):
        """
        Compile and return a dictionary of regex patterns for double parentheses.

        Attributes:
            all: Matches ((...)).
            block_reference: Matches UUID block references.
        """
        self.all = re.compile(
            r"""
            (?<!\{\{embed\ )    # Negative lookbehind: not preceded by "{{embed "
            \(\(                # Opening double parentheses
            .*?                 # Any characters (non-greedy)
            \)\)                # Closing double parentheses
            """,
            re.IGNORECASE | re.VERBOSE,
        )
        self.block_reference = re.compile(
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
        )
        logging.info("Compiled DoubleParenthesesPatterns")

    def process(self, results: List[str]) -> Dict[str, List[str]]:
        """
        Process double parentheses and categorize them.

        Args:
            results (List[str]): List of double parenthesis strings.

        Returns:
            Dict[str, List[str]]: Dictionary categorizing double parentheses.
        """
        if not results:
            return {}

        double_paren_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if self.block_reference.search(result):
                double_paren_family[Criteria.BLOCK_REFERENCES.value].append(result)
                results.pop()
                continue

        double_paren_family[Criteria.REFERENCES_GENERAL.value] = results

        return double_paren_family


@singleton
@dataclass
class EmbeddedLinksPatterns:
    """
    Class to hold regex patterns for embedded links in Logseq content.
    """

    all = None
    internet = None
    asset = None

    def __post_init__(self):
        """
        Compile and return a dictionary of regex patterns for embedded links.

        Attributes:
            all: Matches embedded content links.
            internet: Matches embedded internet content.
            asset: Matches embedded asset references.
        """
        self.all = re.compile(
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
        )
        self.internet = re.compile(
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
        )
        self.asset = re.compile(
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
        )
        logging.info("Compiled EmbeddedLinksPatterns")

    def process(self, results: List[str]) -> Dict[str, List[str]]:
        """
        Process embedded links and categorize them.

        Args:
            results (List[str]): List of embedded link strings.

        Returns:
            Dict[str, List[str]]: Dictionary categorizing embedded links.
        """
        if not results:
            return {}

        embedded_links_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if self.internet.search(result):
                embedded_links_family[Criteria.EMBEDDED_LINKS_INTERNET.value].append(result)
                results.pop()
                continue
            if self.asset.search(result):
                embedded_links_family[Criteria.EMBEDDED_LINKS_ASSET.value].append(result)
                results.pop()
                continue

        embedded_links_family[Criteria.EMBEDDED_LINKS_OTHER.value] = results

        return embedded_links_family


@singleton
@dataclass
class ExternalLinksPatterns:
    """
    Class to hold regex patterns for external links in Logseq content.
    """

    all = None
    internet = None
    alias = None

    def __post_init__(self):
        """
        Compile and return a dictionary of regex patterns for external links.

        Attributes:
            all: Matches markdown-style external links.
            internet: Matches external links to websites (http/https).
            alias: Matches aliased external links (e.g., nested links).
        """
        self.all = re.compile(
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
        )
        self.internet = re.compile(
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
        )
        self.alias = re.compile(
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
        )
        logging.info("Compiled ExternalLinksPatterns")

    def process(self, results: List[str]) -> Dict[str, List[str]]:
        """
        Process external links and categorize them.

        Args:
            results (List[str]): List of external link strings.

        Returns:
            Dict[str, List[str]]: Dictionary categorizing external links.
        """
        if not results:
            return {}

        external_links_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if self.internet.search(result):
                external_links_family[Criteria.EXTERNAL_LINKS_INTERNET.value].append(result)
                results.pop()
                continue
            if self.alias.search(result):
                external_links_family[Criteria.EXTERNAL_LINKS_ALIAS.value].append(result)
                results.pop()
                continue

        external_links_family[Criteria.EXTERNAL_LINKS_OTHER.value] = results

        return external_links_family
