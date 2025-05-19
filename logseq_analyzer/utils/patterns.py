"""
Compile frequently used regex patterns for Logseq content.
"""

import re
from collections import defaultdict

from .enums import Criteria
from .helpers import singleton


@singleton
class ContentPatterns:
    """Class to hold regex patterns for content in Logseq files."""

    bullet = re.compile(
        r"""
        ^           # Beginning of line
        \s*         # Optional whitespace
        -           # Literal hyphen
        \s*         # Optional whitespace
        """,
        re.MULTILINE | re.IGNORECASE | re.VERBOSE,
    )
    page_reference = re.compile(
        r"""
        (?<!\#)     # Negative lookbehind: not preceded by #
        \[\[        # Opening double brackets
        (.+?)       # Capture group: the page name (non-greedy)
        \]\]        # Closing double brackets
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    tagged_backlink = re.compile(
        r"""
        \#          # Hash character
        \[\[        # Opening double brackets
        ([^\]\#]+?) # Anything except closing brackets or hash (non-greedy)
        \]\]        # Closing double brackets
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    tag = re.compile(
        r"""
        \#              # Hash character
        (?!\[\[)        # Negative lookahead: not followed by [[
        ([^\]\#\s]+?)   # Anything except closing brackets, hash, or whitespace (non-greedy)
        (?=\s|$)        # Followed by whitespace or end of line
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    property = re.compile(
        r"""
        ^                   # Start of line
        (?!\s*-\s)          # Negative lookahead: not a bullet
        \s*?                # Optional whitespace
        ([A-Za-z0-9_-]+?)   # Capture group: alphanumeric, underscore, or hyphen (non-greedy)
        (?=::)              # Positive lookahead: double colon
        """,
        re.MULTILINE | re.IGNORECASE | re.VERBOSE,
    )
    property_value = re.compile(
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
    asset = re.compile(
        r"""
        assets/         # assets/ literal string
        (.+)            # Capture group: anything except newline (non-greedy)
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    draw = re.compile(
        r"""
        (?<!\#)             # Negative lookbehind: not preceded by #
        \[\[                # Opening double brackets
        draws/(.+?)         # Literal "draws/" followed by capture group
        \.excalidraw        # Literal ".excalidraw"
        \]\]                # Closing double brackets
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    blockquote = re.compile(
        r"""
        (?:^|\s)            # Start of line or whitespace
        -\ >                # Hyphen, space, greater than
        .*                  # Any characters
        """,
        re.MULTILINE | re.IGNORECASE | re.VERBOSE,
    )
    flashcard = re.compile(
        r"""
        (?:^|\s)            # Start of line or whitespace
        -\ .*               # Hyphen, space, any characters
        \#card|\[\[card\]\] # Either "#card" or "[[card]]"
        .*                  # Any characters
        """,
        re.MULTILINE | re.IGNORECASE | re.VERBOSE,
    )
    dynamic_variable = re.compile(
        r"""
        <%                  # Opening tag
        \s*                 # Optional whitespace
        .*?                 # Any characters (non-greedy)
        \s*                 # Optional whitespace
        %>                  # Closing tag
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    any_link = re.compile(
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
    bold = re.compile(
        r"""
        \*\*                # Opening double asterisks
        .*?                 # Any characters (non-greedy)
        \*\*                # Closing double asterisks
        """,
        re.IGNORECASE | re.VERBOSE,
    )


@singleton
class DoubleCurlyBracketsPatterns:
    """Class to hold regex patterns for double curly brackets in Logseq content."""

    all = re.compile(
        r"""
        \{\{                # Opening double braces
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    embed = re.compile(
        r"""
        \{\{embed\          # "{{embed" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    page_embed = re.compile(
        r"""
        \{\{embed\          # "{{embed" followed by space
        \[\[                # Opening double brackets
        .*?                 # Any characters (non-greedy)
        \]\]                # Closing double brackets
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    block_embed = re.compile(
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
    namespace_query = re.compile(
        r"""
        \{\{namespace\      # "{{namespace" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    card = re.compile(
        r"""
        \{\{cards\          # "{{cards" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    cloze = re.compile(
        r"""
        \{\{cloze\          # "{{cloze" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    simple_query = re.compile(
        r"""
        \{\{query\          # "{{query" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    query_function = re.compile(
        r"""
        \{\{function\       # "{{function" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    embed_video_url = re.compile(
        r"""
        \{\{video\          # "{{video" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    embed_twitter_tweet = re.compile(
        r"""
        \{\{tweet\          # "{{tweet" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    embed_youtube_timestamp = re.compile(
        r"""
        \{\{youtube-timestamp\  # "{{youtube-timestamp" followed by space
        .*?                     # Any characters (non-greedy)
        \}\}                    # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    renderer = re.compile(
        r"""
        \{\{renderer\       # "{{renderer" followed by space
        .*?                 # Any characters (non-greedy)
        \}\}                # Closing double braces
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def process(cls, results: list[str]) -> dict[str, list[str]]:
        """
        Process double curly braces and extract relevant data.

        Args:
            results (list[str]): List of double curly brace strings.

        Returns:
            dict[str, list[str]]: Dictionary categorizing double curly brace data.
        """
        if not results:
            return {}

        double_curly_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if cls.embed.search(result):
                double_curly_family[Criteria.EMBEDS.value].append(result)
                results.pop()
                if cls.page_embed.search(result):
                    double_curly_family[Criteria.PAGE_EMBEDS.value].append(result)
                    double_curly_family[Criteria.EMBEDS.value].remove(result)
                    continue
                if cls.block_embed.search(result):
                    double_curly_family[Criteria.BLOCK_EMBEDS.value].append(result)
                    double_curly_family[Criteria.EMBEDS.value].remove(result)
                    continue
            if cls.namespace_query.search(result):
                double_curly_family[Criteria.NAMESPACE_QUERIES.value].append(result)
                results.pop()
                continue
            if cls.card.search(result):
                double_curly_family[Criteria.CARDS.value].append(result)
                results.pop()
                continue
            if cls.cloze.search(result):
                double_curly_family[Criteria.CLOZES.value].append(result)
                results.pop()
                continue
            if cls.simple_query.search(result):
                double_curly_family[Criteria.SIMPLE_QUERIES.value].append(result)
                results.pop()
                continue
            if cls.query_function.search(result):
                double_curly_family[Criteria.QUERY_FUNCTIONS.value].append(result)
                results.pop()
                continue
            if cls.embed_video_url.search(result):
                double_curly_family[Criteria.EMBED_VIDEO_URLS.value].append(result)
                results.pop()
                continue
            if cls.embed_twitter_tweet.search(result):
                double_curly_family[Criteria.EMBED_TWITTER_TWEETS.value].append(result)
                results.pop()
                continue
            if cls.embed_youtube_timestamp.search(result):
                double_curly_family[Criteria.EMBED_YOUTUBE_TIMESTAMPS.value].append(result)
                results.pop()
                continue
            if cls.renderer.search(result):
                double_curly_family[Criteria.RENDERERS.value].append(result)
                results.pop()
                continue

        double_curly_family[Criteria.MACROS.value] = results

        return double_curly_family


@singleton
class AdvancedCommandPatterns:
    """Class to hold regex patterns for advanced commands in Logseq content."""

    all = re.compile(
        r"""
        \#\+BEGIN_          # "#+BEGIN_"
        .*?                 # Any characters (non-greedy)
        \#\+END_            # "#+END_"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    export = re.compile(
        r"""
        \#\+BEGIN_EXPORT    # "#+BEGIN_EXPORT"
        .*?                 # Any characters (non-greedy)
        \#\+END_EXPORT      # "#+END_EXPORT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    export_ascii = re.compile(
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
    export_latex = re.compile(
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
    caution = re.compile(
        r"""
        \#\+BEGIN_CAUTION   # "#+BEGIN_CAUTION"
        .*?                 # Any characters (non-greedy)
        \#\+END_CAUTION     # "#+END_CAUTION"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    center = re.compile(
        r"""
        \#\+BEGIN_CENTER    # "#+BEGIN_CENTER"
        .*?                 # Any characters (non-greedy)
        \#\+END_CENTER      # "#+END_CENTER"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    comment = re.compile(
        r"""
        \#\+BEGIN_COMMENT   # "#+BEGIN_COMMENT"
        .*?                 # Any characters (non-greedy)
        \#\+END_COMMENT     # "#+END_COMMENT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    example = re.compile(
        r"""
        \#\+BEGIN_EXAMPLE   # "#+BEGIN_EXAMPLE"
        .*?                 # Any characters (non-greedy)
        \#\+END_EXAMPLE     # "#+END_EXAMPLE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    important = re.compile(
        r"""
        \#\+BEGIN_IMPORTANT # "#+BEGIN_IMPORTANT"
        .*?                 # Any characters (non-greedy)
        \#\+END_IMPORTANT   # "#+END_IMPORTANT"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    note = re.compile(
        r"""
        \#\+BEGIN_NOTE      # "#+BEGIN_NOTE"
        .*?                 # Any characters (non-greedy)
        \#\+END_NOTE        # "#+END_NOTE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    pinned = re.compile(
        r"""
        \#\+BEGIN_PINNED    # "#+BEGIN_PINNED"
        .*?                 # Any characters (non-greedy)
        \#\+END_PINNED      # "#+END_PINNED"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    query = re.compile(
        r"""
        \#\+BEGIN_QUERY     # "#+BEGIN_QUERY"
        .*?                 # Any characters (non-greedy)
        \#\+END_QUERY       # "#+END_QUERY"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    quote = re.compile(
        r"""
        \#\+BEGIN_QUOTE     # "#+BEGIN_QUOTE"
        .*?                 # Any characters (non-greedy)
        \#\+END_QUOTE       # "#+END_QUOTE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    tip = re.compile(
        r"""
        \#\+BEGIN_TIP       # "#+BEGIN_TIP"
        .*?                 # Any characters (non-greedy)
        \#\+END_TIP         # "#+END_TIP"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    verse = re.compile(
        r"""
        \#\+BEGIN_VERSE     # "#+BEGIN_VERSE"
        .*?                 # Any characters (non-greedy)
        \#\+END_VERSE       # "#+END_VERSE"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    warning = re.compile(
        r"""
        \#\+BEGIN_WARNING   # "#+BEGIN_WARNING"
        .*?                 # Any characters (non-greedy)
        \#\+END_WARNING     # "#+END_WARNING"
        .*?                 # Any characters (non-greedy)
        (?:\n|$)            # Newline or end-of-file
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def process(cls, results: list[str]) -> dict[str, list[str]]:
        """
        Process advanced commands and extract relevant data.

        Args:
            results (list[str]): List of advanced command strings.

        Returns:
            dict[str, list[str]]: Dictionary categorizing advanced commands.
        """
        if not results:
            return {}

        advanced_command_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if cls.export.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].append(result)
                results.pop()
                if cls.export_ascii.search(result):
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT_ASCII.value].append(result)
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].pop()
                    continue
                if cls.export_latex.search(result):
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT_LATEX.value].append(result)
                    advanced_command_family[Criteria.ADVANCED_COMMANDS_EXPORT.value].pop()
                    continue
            if cls.caution.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_CAUTION.value].append(result)
                results.pop()
                continue
            if cls.center.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_CENTER.value].append(result)
                results.pop()
                continue
            if cls.comment.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_COMMENT.value].append(result)
                results.pop()
                continue
            if cls.example.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_EXAMPLE.value].append(result)
                results.pop()
                continue
            if cls.important.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_IMPORTANT.value].append(result)
                results.pop()
                continue
            if cls.note.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_NOTE.value].append(result)
                results.pop()
                continue
            if cls.pinned.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_PINNED.value].append(result)
                results.pop()
                continue
            if cls.query.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_QUERY.value].append(result)
                results.pop()
                continue
            if cls.quote.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_QUOTE.value].append(result)
                results.pop()
                continue
            if cls.tip.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_TIP.value].append(result)
                results.pop()
                continue
            if cls.verse.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_VERSE.value].append(result)
                results.pop()
                continue
            if cls.warning.search(result):
                advanced_command_family[Criteria.ADVANCED_COMMANDS_WARNING.value].append(result)
                results.pop()
                continue

        advanced_command_family[Criteria.ADVANCED_COMMANDS.value] = results

        return advanced_command_family


@singleton
class CodePatterns:
    """Class to hold regex patterns for code blocks in Logseq content."""

    all = re.compile(
        r"""
        ```                 # Three backticks
        .*?                 # Any characters (non-greedy)
        ```                 # Three backticks
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    multiline_code_lang = re.compile(
        r"""
        ```                 # Three backticks
        \w+                 # One or more word characters
        .*?                 # Any characters (non-greedy)
        ```                 # Three backticks
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    calc_block = re.compile(
        r"""
        ```calc             # Three backticks followed by "calc"
        .*?                 # Any characters (non-greedy)
        ```                 # Three backticks
        """,
        re.DOTALL | re.IGNORECASE | re.VERBOSE,
    )
    inline_code_block = re.compile(
        r"""
        `                   # One backtick
        [^`].+?             # Any characters except backtick (non-greedy)
        `                   # One backtick
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def process(cls, results: list[str]) -> dict[str, list[str]]:
        """
        Process code blocks and categorize them.

        Args:
            results (list[str]): List of code block strings.

        Returns:
            dict[str, list[str]]: Dictionary categorizing code blocks.
        """
        if not results:
            return {}

        code_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if cls.calc_block.search(result):
                code_family[Criteria.CALC_BLOCKS.value].append(result)
                results.pop()
                continue
            if cls.multiline_code_lang.search(result):
                code_family[Criteria.MULTILINE_CODE_LANGS.value].append(result)
                results.pop()
                continue

        code_family[Criteria.MULTILINE_CODE_BLOCKS.value] = results

        return code_family


@singleton
class DoubleParenthesesPatterns:
    """Class to hold regex patterns for double parentheses in Logseq content."""

    all = re.compile(
        r"""
        (?<!\{\{embed\ )    # Negative lookbehind: not preceded by "{{embed "
        \(\(                # Opening double parentheses
        .*?                 # Any characters (non-greedy)
        \)\)                # Closing double parentheses
        """,
        re.IGNORECASE | re.VERBOSE,
    )
    block_reference = re.compile(
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

    @classmethod
    def process(cls, results: list[str]) -> dict[str, list[str]]:
        """
        Process double parentheses and categorize them.

        Args:
            results (list[str]): List of double parenthesis strings.

        Returns:
            dict[str, list[str]]: Dictionary categorizing double parentheses.
        """
        if not results:
            return {}

        double_paren_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if cls.block_reference.search(result):
                double_paren_family[Criteria.BLOCK_REFERENCES.value].append(result)
                results.pop()
                continue

        double_paren_family[Criteria.REFERENCES_GENERAL.value] = results

        return double_paren_family


@singleton
class EmbeddedLinksPatterns:
    """Class to hold regex patterns for embedded links in Logseq content."""

    all = re.compile(
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
    internet = re.compile(
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
    asset = re.compile(
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

    @classmethod
    def process(cls, results: list[str]) -> dict[str, list[str]]:
        """
        Process embedded links and categorize them.

        Args:
            results (list[str]): List of embedded link strings.

        Returns:
            dict[str, list[str]]: Dictionary categorizing embedded links.
        """
        if not results:
            return {}

        embedded_links_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if cls.internet.search(result):
                embedded_links_family[Criteria.EMBEDDED_LINKS_INTERNET.value].append(result)
                results.pop()
                continue
            if cls.asset.search(result):
                embedded_links_family[Criteria.EMBEDDED_LINKS_ASSET.value].append(result)
                results.pop()
                continue

        embedded_links_family[Criteria.EMBEDDED_LINKS_OTHER.value] = results

        return embedded_links_family


@singleton
class ExternalLinksPatterns:
    """Class to hold regex patterns for external links in Logseq content."""

    all = re.compile(
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
    internet = re.compile(
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
    alias = re.compile(
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

    @classmethod
    def process(cls, results: list[str]) -> dict[str, list[str]]:
        """
        Process external links and categorize them.

        Args:
            results (list[str]): List of external link strings.

        Returns:
            dict[str, list[str]]: Dictionary categorizing external links.
        """
        if not results:
            return {}

        external_links_family = defaultdict(list)

        for _ in range(len(results)):
            result = results[-1]
            if cls.internet.search(result):
                external_links_family[Criteria.EXTERNAL_LINKS_INTERNET.value].append(result)
                results.pop()
                continue
            if cls.alias.search(result):
                external_links_family[Criteria.EXTERNAL_LINKS_ALIAS.value].append(result)
                results.pop()
                continue

        external_links_family[Criteria.EXTERNAL_LINKS_OTHER.value] = results

        return external_links_family
