"""
This module handles processing of Logseq filenames based on their parent directory.
"""

from calendar import c
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from urllib.parse import unquote

from ._global_objects import ANALYZER_CONFIG


@dataclass
class LogseqFilename:
    """Class for processing Logseq filenames based on their parent directory."""

    file_path: Path

    def __post_init__(self):
        """Initialize the LogseqFilename class."""
        self.original_name = self.file_path.stem
        self.name = self.file_path.stem.lower()
        self.parent = self.file_path.parent.name.lower()
        self.process_logseq_filename()
        self.id = self.name[:2] if len(self.name) > 1 else f"!{self.name[0]}"
        self.suffix = self.file_path.suffix.lower() if self.file_path.suffix else None
        self.file_path_parts = self.file_path.parts
        self.name_secondary = f"{self.name} {self.parent} + {self.suffix}"
        self.uri = self.file_path.as_uri()
        self.logseq_url = self.convert_uri_to_logseq_url()

    def process_logseq_filename(self):
        """Process the Logseq filename based on its parent directory."""
        ns_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")
        ns_file_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP")
        dir_journals = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "DIR_JOURNALS")

        if self.name.endswith(ns_file_sep):
            self.name = self.name.rstrip(ns_file_sep)

        if self.parent == dir_journals:
            self.process_logseq_journal_key()
        else:
            self.name = unquote(self.name).replace(ns_file_sep, ns_sep)

    def process_logseq_journal_key(self) -> str:
        """Process the journal key to create a page title."""
        journal_page_format = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "JOURNAL_PAGE_TITLE_FORMAT")
        journal_file_format = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "JOURNAL_FILE_NAME_FORMAT")

        py_file_name_format = ANALYZER_CONFIG.get("LOGSEQ_JOURNALS", "PY_FILE_FORMAT")
        if not py_file_name_format:
            py_file_name_format = LogseqFilename.convert_cljs_date_to_py(journal_file_format)
            ANALYZER_CONFIG.set("LOGSEQ_JOURNALS", "PY_FILE_FORMAT", py_file_name_format)

        py_page_title_no_ordinal = journal_page_format.replace("o", "")

        py_page_title_format_base = ANALYZER_CONFIG.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT")
        if not py_page_title_format_base:
            py_page_title_format_base = LogseqFilename.convert_cljs_date_to_py(py_page_title_no_ordinal)
            ANALYZER_CONFIG.set("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT", py_page_title_format_base)

        try:
            date_object = datetime.strptime(self.name, py_file_name_format)
            page_title_base = date_object.strftime(py_page_title_format_base).lower()
            if "o" in journal_page_format:
                day_number = date_object.day
                day_with_ordinal = LogseqFilename.add_ordinal_suffix_to_day_of_month(day_number)
                page_title = page_title_base.replace(
                    f"{day_number}", day_with_ordinal, 1
                )  # Just 1st occurrence, may break with odd implementations
            else:
                page_title = page_title_base
            self.name = page_title.replace("'", "")
        except ValueError as e:
            logging.warning("Failed to parse date from key '%s', format `%s`: %s", self.name, py_file_name_format, e)
            self.name = self.name

    def convert_uri_to_logseq_url(self):
        """Convert a file URI to a Logseq URL."""
        len_uri = len(Path(self.uri).parts)
        len_graph_dir = len(Path(ANALYZER_CONFIG.get("CONST", "GRAPH_DIR")).parts)
        target_index = len_uri - len_graph_dir
        target_segment = Path(self.uri).parts[target_index]
        if target_segment[:-1] not in ("page", "block-id"):
            return ""

        prefix = f"file:///C:/Logseq/{target_segment}/"
        if not self.uri.startswith(prefix):
            return ""

        len_suffix = len(Path(self.uri).suffix)
        path_without_prefix = self.uri[len(prefix) : -(len_suffix)]
        path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
        encoded_path = path_with_slashes
        target_segment = target_segment[:-1]
        return f"logseq://graph/Logseq?{target_segment}={encoded_path}"

    @staticmethod
    def convert_cljs_date_to_py(cljs_format) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.

        Args:
            cljs_format (str): Clojure-style date format.

        Returns:
            str: Python-style date format.
        """
        cljs_format = cljs_format.replace("o", "")

        def replace_token(match):
            token = match.group(0)
            return ANALYZER_CONFIG.datetime_token_map.get(token, token)

        return ANALYZER_CONFIG.datetime_token_pattern.sub(replace_token, cljs_format)

    @staticmethod
    def add_ordinal_suffix_to_day_of_month(day):
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return str(day) + suffix
