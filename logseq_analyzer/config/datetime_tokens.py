"""
Logseq DateTime Tokens Module
"""

import re

from .analyzer_config import LogseqAnalyzerConfig
from .graph_config import LogseqGraphConfig


class LogseqDateTimeTokens:
    """
    Class to handle date and time tokens in Logseq.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the LogseqDateTimeTokens class.
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.analyzer_config = LogseqAnalyzerConfig()
            self.graph_config = LogseqGraphConfig()
            self.token_map = None
            self.token_pattern = None

    def get_datetime_token_map(self):
        """Return the datetime token mapping as a dictionary"""
        self.token_map = self.analyzer_config.get_section("DATETIME_TOKEN_MAP")

    def set_datetime_token_pattern(self):
        """Return a compiled regex pattern for datetime tokens"""
        tokens = self.token_map.keys()
        pattern = "|".join(re.escape(k) for k in sorted(tokens, key=len, reverse=True))
        self.token_pattern = re.compile(pattern)

    def set_journal_py_formatting(self):
        """
        Set the formatting for journal files and pages in Python format.
        """
        journal_file_format = self.graph_config.ls_config.get(":journal/file-name-format")
        py_file_fmt = LogseqJournalPyFileFormat()
        if not py_file_fmt.py_file_format:
            py_file_fmt.py_file_format = self.convert_cljs_date_to_py(journal_file_format)

        journal_page_format = self.graph_config.ls_config.get(":journal/page-title-format")
        py_page_title_no_ordinal = journal_page_format.replace("o", "")
        py_page_fmt = LogseqJournalPyPageFormat()
        if not py_page_fmt.py_page_format:
            py_page_fmt.py_page_format = self.convert_cljs_date_to_py(py_page_title_no_ordinal)

    def convert_cljs_date_to_py(self, cljs_format) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.
        """
        cljs_format = cljs_format.replace("o", "")
        return self.token_pattern.sub(self.replace_token, cljs_format)

    def replace_token(self, match):
        """
        Replace a date token with its corresponding Python format.
        """
        token = match.group(0)
        return self.token_map.get(token, token)


class LogseqJournalPyFileFormat:
    """
    Class to handle the Python file format for Logseq journals.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the LogseqJournalPyFileFormat class.
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.py_file_format = ""

    def __str__(self):
        """Return the string representation of the LogseqJournalPyFileFormat."""
        return self.py_file_format

    @property
    def py_file_format(self):
        """Return the Python file format for Logseq journals."""
        return self._py_file_format

    @py_file_format.setter
    def py_file_format(self, value):
        """Set the Python file format for Logseq journals."""
        if not isinstance(value, str):
            raise ValueError("File format must be a string.")
        self._py_file_format = value

    @py_file_format.deleter
    def py_file_format(self):
        """Delete the Python file format for Logseq journals."""
        del self._py_file_format


class LogseqJournalPyPageFormat:
    """
    Class to handle the Python name format for Logseq journals.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the LogseqJournalPyNameFormat class.
        """
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.py_page_format = ""

    def __str__(self):
        """Return the string representation of the LogseqJournalPyPageFormat."""
        return self.py_page_format

    @property
    def py_page_format(self):
        """Return the Python name format for Logseq journals."""
        return self._py_page_format

    @py_page_format.setter
    def py_page_format(self, value):
        """Set the Python name format for Logseq journals."""
        if not isinstance(value, str):
            raise ValueError("File format must be a string.")
        self._py_page_format = value

    @py_page_format.deleter
    def py_page_format(self):
        """Delete the Python name format for Logseq journals."""
        del self._py_page_format
