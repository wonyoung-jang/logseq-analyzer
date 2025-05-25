"""
Logseq DateTime Tokens Module
"""

import logging
import re

from ..utils.helpers import singleton


DATETIME_TOKEN_MAP = {
    "yyyy": "%Y",
    "xxxx": "%Y",
    "yy": "%y",
    "xx": "%y",
    "MMMM": "%B",
    "MMM": "%b",
    "MM": "%m",
    "M": "%#m",
    "dd": "%d",
    "d": "%#d",
    "D": "%j",
    "EEEE": "%A",
    "EEE": "%a",
    "EE": "%a",
    "E": "%a",
    "e": "%u",
    "HH": "%H",
    "H": "%H",
    "hh": "%I",
    "h": "%I",
    "mm": "%M",
    "m": "%#M",
    "ss": "%S",
    "s": "%#S",
    "SSS": "%f",
    "a": "%p",
    "A": "%p",
    "Z": "%z",
    "ZZ": "%z",
}


@singleton
class LogseqJournalFormats:
    """
    Class to handle the Python file format for Logseq journals.
    """

    __slots__ = ("_file", "_page")

    def __init__(self) -> None:
        """
        Initialize the LogseqJournalFormats class.
        """
        self._file: str = ""
        self._page: str = ""

    @property
    def file(self) -> str:
        """Return the Python file format for Logseq journals."""
        return self._file

    @file.setter
    def file(self, value) -> None:
        """Set the Python file format for Logseq journals."""
        if not isinstance(value, str):
            raise ValueError("File format must be a string.")
        self._file = value

    @property
    def page(self) -> str:
        """Return the Python name format for Logseq journals."""
        return self._page

    @page.setter
    def page(self, value) -> None:
        """Set the Python name format for Logseq journals."""
        if not isinstance(value, str):
            raise ValueError("File format must be a string.")
        self._page = value


@singleton
class LogseqDateTimeTokens:
    """
    Class to handle date and time tokens in Logseq.
    """

    __slots__ = ("_token_map", "_token_pattern")

    def __init__(self) -> None:
        """
        Initialize the LogseqDateTimeTokens class.
        """
        self._token_map = DATETIME_TOKEN_MAP
        self._token_pattern = None

    def set_datetime_token_pattern(self) -> None:
        """Return a compiled regex pattern for datetime tokens"""
        tokens = self._token_map.keys()
        pattern = "|".join(re.escape(k) for k in sorted(tokens, key=len, reverse=True))
        self._token_pattern = re.compile(pattern)
        logging.debug("LogseqDateTimeTokens: set_datetime_token_pattern()")

    def set_journal_py_formatting(self, graph_config: dict[str, str], ljf: LogseqJournalFormats) -> None:
        """
        Set the formatting for journal files and pages in Python format.
        """
        journal_file_format = graph_config.get(":journal/file-name-format")
        journal_page_format = graph_config.get(":journal/page-title-format")
        ljf.file = self.convert_cljs_date_to_py(journal_file_format)
        ljf.page = self.convert_cljs_date_to_py(journal_page_format)
        logging.debug("LogseqDateTimeTokens: set_journal_py_formatting()")

    def convert_cljs_date_to_py(self, cljs_format: str) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.
        """
        cljs_format = cljs_format.replace("o", "")
        logging.debug("LogseqDateTimeTokens: _convert_cljs_date_to_py()")
        return self._token_pattern.sub(self.replace_token, cljs_format)

    def replace_token(self, match: re.Match) -> str:
        """
        Replace a date token with its corresponding Python format.
        """
        token = match.group(0)
        logging.debug("LogseqDateTimeTokens: _replace_token()")
        return self._token_map.get(token, token)
