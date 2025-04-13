"""
Logseq DateTime Tokens Module
"""

import re

from .analyzer_config import LogseqAnalyzerConfig


class LogseqDateTimeTokens:
    """
    Class to handle date and time tokens in Logseq.
    """

    _instance = None

    def __new__(cls, *args):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, analyzer_config: LogseqAnalyzerConfig = None):
        """
        Initialize the LogseqDateTimeTokens class.
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.analyzer_config = analyzer_config
            self.datetime_token_map = None
            self.datetime_token_pattern = None

    def get_datetime_token_map(self):
        """Return the datetime token mapping as a dictionary"""
        self.datetime_token_map = self.analyzer_config.get_section("DATETIME_TOKEN_MAP")

    def set_datetime_token_pattern(self):
        """Return a compiled regex pattern for datetime tokens"""
        tokens = self.datetime_token_map.keys()
        pattern = "|".join(re.escape(k) for k in sorted(tokens, key=len, reverse=True))
        self.datetime_token_pattern = re.compile(pattern)

    def set_journal_py_formatting(self):
        """
        Set the formatting for journal files and pages in Python format.
        """
        journal_page_format = self.analyzer_config.get("LOGSEQ_CONFIG", "JOURNAL_PAGE_TITLE_FORMAT")
        journal_file_format = self.analyzer_config.get("LOGSEQ_CONFIG", "JOURNAL_FILE_NAME_FORMAT")
        if not self.analyzer_config.get("LOGSEQ_JOURNALS", "PY_FILE_FORMAT"):
            py_file_name_format = self.convert_cljs_date_to_py(journal_file_format)
            self.analyzer_config.set("LOGSEQ_JOURNALS", "PY_FILE_FORMAT", py_file_name_format)
        py_page_title_no_ordinal = journal_page_format.replace("o", "")
        if not self.analyzer_config.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT"):
            py_page_title_format_base = self.convert_cljs_date_to_py(py_page_title_no_ordinal)
            self.analyzer_config.set("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT", py_page_title_format_base)

    def convert_cljs_date_to_py(self, cljs_format) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.
        """
        cljs_format = cljs_format.replace("o", "")
        return self.datetime_token_pattern.sub(self.replace_token, cljs_format)

    def replace_token(self, match):
        """
        Replace a date token with its corresponding Python format.
        """
        token = match.group(0)
        return self.datetime_token_map.get(token, token)
