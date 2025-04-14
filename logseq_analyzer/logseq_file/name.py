"""
This module handles processing of Logseq filenames based on their parent directory.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import logging

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
    file_type: str = None
    ac: LogseqAnalyzerConfig = LogseqAnalyzerConfig()

    def __post_init__(self):
        """Initialize the LogseqFilename class."""
        self.original_name = self.file_path.stem
        self.name = self.file_path.stem.lower()
        self.parent = self.file_path.parent.name.lower()
        self.suffix = self.file_path.suffix.lower() if self.file_path.suffix else None
        self.parts = self.file_path.parts
        self.uri = self.file_path.as_uri()
        self.is_namespace = False
        self.logseq_url = ""
        self.file_type = ""

    def process_logseq_filename(self):
        """Process the Logseq filename based on its parent directory."""
        if self.name.endswith(self.ac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"]):
            self.name = self.name.rstrip(self.ac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"])

        if self.parent == self.ac.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]:
            self.process_logseq_journal_key()
        else:
            self.name = unquote(self.name).replace(self.ac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"], NS_SEP)

        self.is_namespace = NS_SEP in self.name

    def process_logseq_journal_key(self):
        """Process the journal key to create a page title."""
        try:
            date_object = datetime.strptime(self.name, self.ac.config["LOGSEQ_JOURNALS"]["PY_FILE_FORMAT"])
            page_title_base = date_object.strftime(self.ac.config["LOGSEQ_JOURNALS"]["PY_PAGE_BASE_FORMAT"]).lower()
            if "o" in self.ac.config["LOGSEQ_CONFIG"]["JOURNAL_PAGE_TITLE_FORMAT"]:
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
                self.ac.config["LOGSEQ_JOURNALS"]["PY_FILE_FORMAT"],
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
        self.file_type = {
            self.ac.config["LOGSEQ_CONFIG"]["DIR_ASSETS"]: "asset",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_DRAWS"]: "draw",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]: "journal",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_PAGES"]: "page",
            self.ac.config["LOGSEQ_CONFIG"]["DIR_WHITEBOARDS"]: "whiteboard",
        }.get(self.parent, "other")

    @staticmethod
    def add_ordinal_suffix_to_day_of_month(day):
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return str(day) + suffix
