"""
This module handles processing of Logseq filenames based on their parent directory.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..config.datetime_tokens import LogseqJournalFormats
from ..config.graph_config import LogseqGraphConfig
from ..io.filesystem import GraphDirectory
from ..utils.enums import Core

DATE_ORDINAL_SUFFIX = "o"


@dataclass
class LogseqFilename:
    """
    LogseqFilename class.
    """

    file_path: Path
    name: str = field(init=False, repr=False)
    parent: str = field(init=False, repr=False)
    suffix: str = field(init=False, repr=False)
    parts: tuple = field(init=False, repr=False)
    uri: str = field(init=False, repr=False)
    logseq_url: str = field(init=False, repr=False)
    file_type: str = field(init=False, repr=False)
    is_namespace: bool = field(init=False, repr=False)
    is_hls: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqFilename class."""
        path = self.file_path
        self.name = path.stem
        self.parent = path.parent.name
        self.suffix = path.suffix if path.suffix else ""
        self.parts = path.parts
        self.uri = path.as_uri()

    def process_logseq_filename(self) -> None:
        """Process the Logseq filename based on its parent directory."""
        lac = LogseqAnalyzerConfig()
        ns_file_sep = lac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"]
        name = self.name.strip(ns_file_sep)
        if self.parent == lac.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]:
            self.name = LogseqFilename._process_logseq_journal_key(name)
        else:
            self.name = unquote(name).replace(ns_file_sep, Core.NS_SEP.value)

    def check_is_namespace(self) -> None:
        """Check if the filename is a namespace."""
        self.is_namespace = Core.NS_SEP.value in self.name

    def check_is_hls(self) -> None:
        """Check if the filename is a HLS (Hierarchical Logseq Structure)."""
        self.is_hls = self.name.startswith(Core.HLS_PREFIX.value)

    def convert_uri_to_logseq_url(self) -> None:
        """Convert a file URI to a Logseq URL."""
        uri = self.uri
        uri_path = Path(uri)
        gd = GraphDirectory()
        len_gd = len(gd.path.parts)
        len_uri = len(uri_path.parts)
        target_index = len_uri - len_gd
        target_segment = uri_path.parts[target_index]
        if target_segment[:-1] in ("page", "block-id"):
            prefix = f"file:///{str(gd.path)}/{target_segment}/"
            if uri.startswith(prefix):
                len_suffix = len(uri_path.suffix)
                path_without_prefix = uri[len(prefix) : -(len_suffix)]
                path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
                encoded_path = path_with_slashes
                target_segment = target_segment[:-1]
                self.logseq_url = f"logseq://graph/Logseq?{target_segment}={encoded_path}"

    def get_namespace_name_data(self) -> None:
        """Get the namespace name data."""
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

    def determine_file_type(self) -> None:
        """
        Helper function to determine the file type based on the directory structure.
        """
        lac = LogseqAnalyzerConfig()
        config = lac.config["LOGSEQ_CONFIG"]
        result = {
            config["DIR_ASSETS"]: "asset",
            config["DIR_DRAWS"]: "draw",
            config["DIR_JOURNALS"]: "journal",
            config["DIR_PAGES"]: "page",
            config["DIR_WHITEBOARDS"]: "whiteboard",
        }.get(self.parent, "other")

        if result != "other":
            self.file_type = result
        else:
            parts = self.parts
            if config["DIR_ASSETS"] in parts:
                result = "sub_asset"
            elif config["DIR_DRAWS"] in parts:
                result = "sub_draw"
            elif config["DIR_JOURNALS"] in parts:
                result = "sub_journal"
            elif config["DIR_PAGES"] in parts:
                result = "sub_page"
            elif config["DIR_WHITEBOARDS"] in parts:
                result = "sub_whiteboard"
            self.file_type = result

    @staticmethod
    def _process_logseq_journal_key(name: str) -> str:
        """Process the journal key to create a page title."""
        try:
            ljf = LogseqJournalFormats()
            lgc = LogseqGraphConfig()
            date_object = datetime.strptime(name, ljf.file)
            page_title_base = date_object.strftime(ljf.page)
            if DATE_ORDINAL_SUFFIX in lgc.config_merged.get(":journal/page-title-format"):
                day_number = date_object.day
                day_with_ordinal = LogseqFilename._add_ordinal_suffix_to_day_of_month(day_number)
                page_title = page_title_base.replace(str(day_number), day_with_ordinal, 1)
            else:
                page_title = page_title_base
            page_title = page_title.replace("'", "")
            return page_title
        except ValueError as e:
            logging.warning("Failed to parse date from key '%s', format `%s`: %s", name, ljf.page, e)
            return ""

    @staticmethod
    def _add_ordinal_suffix_to_day_of_month(day) -> str:
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return str(day) + suffix
