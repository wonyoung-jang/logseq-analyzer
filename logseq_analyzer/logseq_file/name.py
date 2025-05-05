"""
This module handles processing of Logseq filenames based on their parent directory.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import logging

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..config.datetime_tokens import LogseqJournalFormats
from ..config.graph_config import LogseqGraphConfig
from ..io.filesystem import GraphDirectory
from ..utils.enums import Core


DATE_ORDINAL_SUFFIX = "o"


@dataclass
class LogseqFilename:
    """Class for processing Logseq filenames based on their parent directory."""

    file_path: Path

    original_name: str = ""
    name: str = ""
    parent: str = ""
    suffix: str = ""
    parts: tuple = ()
    uri: str = ""
    logseq_url: str = ""
    file_type: str = ""
    is_namespace: bool = False
    is_hls: bool = False

    def __post_init__(self):
        """Initialize the LogseqFilename class."""
        self.original_name = self.file_path.stem
        self.name = self.file_path.stem.lower()
        self.parent = self.file_path.parent.name.lower()
        self.suffix = self.file_path.suffix.lower() if self.file_path.suffix else ""
        self.parts = self.file_path.parts
        self.uri = self.file_path.as_uri()

    def __repr__(self):
        return f'LogseqFilename(file_path="{self.file_path}")'

    def __str__(self):
        return f"LogseqFilename: {self.file_path}"

    def process_logseq_filename(self):
        """Process the Logseq filename based on its parent directory."""
        ls_analyzer_config = LogseqAnalyzerConfig()
        ns_file_sep = ls_analyzer_config.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"]

        self.name = self.name.strip(ns_file_sep)

        if self.parent == ls_analyzer_config.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]:
            self.process_logseq_journal_key()
        else:
            self.name = unquote(self.name).replace(ns_file_sep, Core.NS_SEP.value)

        self.is_namespace = Core.NS_SEP.value in self.name
        self.is_hls = self.name.startswith(Core.HLS_PREFIX.value)

    def process_logseq_journal_key(self):
        """Process the journal key to create a page title."""
        ls_journal_formats = LogseqJournalFormats()
        py_file_format = ls_journal_formats.file
        py_page_format = ls_journal_formats.page
        try:
            date_object = datetime.strptime(self.name, py_file_format)
            page_title_base = date_object.strftime(py_page_format).lower()
            lgc = LogseqGraphConfig()
            ls_config = lgc.ls_config
            if DATE_ORDINAL_SUFFIX in ls_config.get(":journal/page-title-format"):
                day_number = date_object.day
                day_with_ordinal = LogseqFilename.add_ordinal_suffix_to_day_of_month(day_number)
                page_title = page_title_base.replace(str(day_number), day_with_ordinal, 1)
            else:
                page_title = page_title_base
            self.name = page_title.replace("'", "")
        except ValueError as e:
            logging.warning("Failed to parse date from key '%s', format `%s`: %s", self.name, py_page_format, e)

    def convert_uri_to_logseq_url(self):
        """Convert a file URI to a Logseq URL."""
        len_uri = len(Path(self.uri).parts)
        graph_dir_path = GraphDirectory().path
        len_graph_dir = len(graph_dir_path.parts)
        target_index = len_uri - len_graph_dir
        target_segment = Path(self.uri).parts[target_index]

        if target_segment[:-1] not in ("page", "block-id"):
            return

        prefix = f"file:///{str(graph_dir_path)}/{target_segment}/"
        if not self.uri.startswith(prefix):
            return

        len_suffix = len(Path(self.uri).suffix)
        path_without_prefix = self.uri[len(prefix) : -(len_suffix)]
        path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
        encoded_path = path_with_slashes
        target_segment = target_segment[:-1]
        self.logseq_url = f"logseq://graph/Logseq?{target_segment}={encoded_path}"

    def get_namespace_name_data(self):
        """Get the namespace name data."""
        if not self.is_namespace:
            return

        ns_parts_list = self.name.split(Core.NS_SEP.value)
        ns_level = len(ns_parts_list)
        ns_root = ns_parts_list[0]
        namespace_name_data = {
            "ns_parts": {part: level for level, part in enumerate(ns_parts_list, start=1)},
            "ns_level": ns_level,
            "ns_root": ns_root,
            "ns_parent": ns_parts_list[-2] if ns_level > 2 else ns_root,
            "ns_parent_full": Core.NS_SEP.value.join(ns_parts_list[:-1]),
            "ns_stem": ns_parts_list[-1],
        }

        for key, value in namespace_name_data.items():
            if value:
                setattr(self, key, value)

    def determine_file_type(self):
        """
        Helper function to determine the file type based on the directory structure.
        """
        result = {
            LogseqAnalyzerConfig().config["LOGSEQ_CONFIG"]["DIR_ASSETS"]: "asset",
            LogseqAnalyzerConfig().config["LOGSEQ_CONFIG"]["DIR_DRAWS"]: "draw",
            LogseqAnalyzerConfig().config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]: "journal",
            LogseqAnalyzerConfig().config["LOGSEQ_CONFIG"]["DIR_PAGES"]: "page",
            LogseqAnalyzerConfig().config["LOGSEQ_CONFIG"]["DIR_WHITEBOARDS"]: "whiteboard",
        }.get(self.parent, "other")

        if result != "other":
            self.file_type = result
            return

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
