"""
This module handles processing of Logseq filenames based on their parent directory.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import logging

from ..config.datetime_tokens import LogseqJournalPyFileFormat, LogseqJournalPyPageFormat
from ..config.graph_config import LogseqGraphConfig
from ..utils.enums import Core
from ..config.analyzer_config import LogseqAnalyzerConfig


NS_SEP = Core.NS_SEP.value


@dataclass
class LogseqFilename:
    """Class for processing Logseq filenames based on their parent directory."""

    file_path: Path
    original_name: str = None
    name: str = None
    parent: str = None
    suffix: str = None
    parts: tuple = None
    uri: str = None
    logseq_url: str = None
    is_namespace: bool = None
    is_hls: bool = None
    file_type: str = None
    ac: LogseqAnalyzerConfig = LogseqAnalyzerConfig()
    gc: LogseqGraphConfig = LogseqGraphConfig()

    def __post_init__(self):
        """Initialize the LogseqFilename class."""
        self.original_name = self.file_path.stem
        self.name = self.file_path.stem.lower()
        self.parent = self.file_path.parent.name.lower()
        self.suffix = self.file_path.suffix.lower() if self.file_path.suffix else None
        self.parts = self.file_path.parts
        self.uri = self.file_path.as_uri()
        self.is_namespace = False
        self.is_hls = False
        self.logseq_url = ""
        self.file_type = ""
        self.py_file_fmt = LogseqJournalPyFileFormat()
        self.py_page_fmt = LogseqJournalPyPageFormat()

    def __repr__(self):
        return f"LogseqFilename({self.file_path})"

    def process_logseq_filename(self):
        """Process the Logseq filename based on its parent directory."""
        if self.name.endswith(self.ac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"]):
            self.name = self.name.rstrip(self.ac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"])

        if self.parent == self.ac.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]:
            self.process_logseq_journal_key()
        else:
            self.name = unquote(self.name).replace(self.ac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"], NS_SEP)

        self.is_namespace = NS_SEP in self.name
        self.is_hls = self.name.startswith(Core.HLS_PREFIX.value)

    def process_logseq_journal_key(self):
        """Process the journal key to create a page title."""
        try:
            date_object = datetime.strptime(self.name, self.py_file_fmt.py_file_format)
            page_title_base = date_object.strftime(self.py_page_fmt.py_page_format).lower()
            if "o" in self.gc.ls_config.get(":journal/page-title-format"):
                day_number = date_object.day
                day_with_ordinal = LogseqFilename.add_ordinal_suffix_to_day_of_month(day_number)
                page_title = page_title_base.replace(
                    f"{day_number}", day_with_ordinal, 1
                )  # Just 1st occurrence, may break with odd implementations
            else:
                page_title = page_title_base
            self.name = page_title.replace("'", "")
        except ValueError as e:
            logging.warning(
                "Failed to parse date from key '%s', format `%s`: %s",
                self.name,
                self.py_page_fmt.py_page_format,
                e,
            )

    def convert_uri_to_logseq_url(self):
        """Convert a file URI to a Logseq URL."""
        len_uri = len(Path(self.uri).parts)
        graph_dir = self.ac.config["ANALYZER"]["GRAPH_DIR"]
        len_graph_dir = len(Path(graph_dir).parts)
        target_index = len_uri - len_graph_dir
        target_segment = Path(self.uri).parts[target_index]
        if target_segment[:-1] in ("page", "block-id"):
            prefix = f"file:///{str(graph_dir)}/{target_segment}/"
            if self.uri.startswith(prefix):
                len_suffix = len(Path(self.uri).suffix)
                path_without_prefix = self.uri[len(prefix) : -(len_suffix)]
                path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
                encoded_path = path_with_slashes
                target_segment = target_segment[:-1]
                self.logseq_url = f"logseq://graph/Logseq?{target_segment}={encoded_path}"

    def get_namespace_name_data(self):
        """Get the namespace name data."""
        if self.is_namespace:
            ns_parts_list = self.name.split(NS_SEP)
            ns_level = len(ns_parts_list)
            ns_root = ns_parts_list[0]
            ns_stem = ns_parts_list[-1]
            ns_parent = ns_root
            if ns_level > 2:
                ns_parent = ns_parts_list[-2]
            ns_parent_full = NS_SEP.join(ns_parts_list[:-1])
            ns_parts = {part: level for level, part in enumerate(ns_parts_list, start=1)}
            namespace_name_data = {
                "ns_parts": ns_parts,
                "ns_level": ns_level,
                "ns_root": ns_root,
                "ns_parent": ns_parent,
                "ns_parent_full": ns_parent_full,
                "ns_stem": ns_stem,
            }
            for key, value in namespace_name_data.items():
                if value:
                    setattr(self, key, value)

    def determine_file_type(self):
        """
        Helper function to determine the file type based on the directory structure.
        """
        result = {
            self.ac.config["LOGSEQ_CONFIG"]["DIR_ASSETS"]: "asset",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_DRAWS"]: "draw",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]: "journal",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_PAGES"]: "page",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_WHITEBOARDS"]: "whiteboard",
        }.get(self.parent, "other")

        if result == "other":
            if "assets" in self.parts:
                result = "sub_asset"
            elif "draws" in self.parts:
                result = "sub_draw"
            elif "journals" in self.parts:
                result = "sub_journal"
            elif "pages" in self.parts:
                result = "sub_page"
            elif "whiteboards" in self.parts:
                result = "sub_whiteboard"

        self.file_type = result

    @staticmethod
    def add_ordinal_suffix_to_day_of_month(day):
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return str(day) + suffix
