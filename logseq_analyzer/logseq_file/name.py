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
    """
    LogseqFilename class.

    Args:
        file_path (Path): The path to the Logseq file.
    """

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

    def __post_init__(self) -> None:
        """Initialize the LogseqFilename class."""
        self.original_name = self.file_path.stem
        self.name = self.file_path.stem.lower()
        self.parent = self.file_path.parent.name.lower()
        self.suffix = self.file_path.suffix.lower() if self.file_path.suffix else ""
        self.parts = self.file_path.parts
        self.uri = self.file_path.as_uri()

    def process_logseq_filename(self) -> str:
        """Process the Logseq filename based on its parent directory."""
        lac = LogseqAnalyzerConfig()
        ns_file_sep = lac.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"]
        name = self.name.strip(ns_file_sep)
        if self.parent == lac.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"]:
            return self._process_logseq_journal_key(name)
        name = unquote(name).replace(ns_file_sep, Core.NS_SEP.value)
        return name

    def check_is_namespace(self) -> bool:
        """Check if the filename is a namespace."""
        return Core.NS_SEP.value in self.name

    def check_is_hls(self) -> bool:
        """Check if the filename is a HLS (Hierarchical Logseq Structure)."""
        return self.name.startswith(Core.HLS_PREFIX.value)

    def _process_logseq_journal_key(self, name: str) -> str:
        """Process the journal key to create a page title."""
        try:
            ljf = LogseqJournalFormats()
            py_file_format = ljf.file
            py_page_format = ljf.page
            date_object = datetime.strptime(name, py_file_format)
            page_title_base = date_object.strftime(py_page_format).lower()
            lgc = LogseqGraphConfig()
            ls_config = lgc.ls_config
            if DATE_ORDINAL_SUFFIX in ls_config.get(":journal/page-title-format"):
                day_number = date_object.day
                day_with_ordinal = LogseqFilename.add_ordinal_suffix_to_day_of_month(day_number)
                page_title = page_title_base.replace(str(day_number), day_with_ordinal, 1)
            else:
                page_title = page_title_base
            page_title = page_title.replace("'", "")
            return page_title
        except ValueError as e:
            logging.warning("Failed to parse date from key '%s', format `%s`: %s", name, py_page_format, e)
            return ""

    def convert_uri_to_logseq_url(self) -> str:
        """Convert a file URI to a Logseq URL."""
        gd = GraphDirectory()
        len_gd = len(gd.path.parts)
        len_uri = len(Path(self.uri).parts)
        target_index = len_uri - len_gd
        target_segment = Path(self.uri).parts[target_index]

        if target_segment[:-1] not in ("page", "block-id"):
            return ""

        prefix = f"file:///{str(gd.path)}/{target_segment}/"
        if not self.uri.startswith(prefix):
            return ""

        len_suffix = len(Path(self.uri).suffix)
        path_without_prefix = self.uri[len(prefix) : -(len_suffix)]
        path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
        encoded_path = path_with_slashes
        target_segment = target_segment[:-1]
        return f"logseq://graph/Logseq?{target_segment}={encoded_path}"

    def get_namespace_name_data(self) -> None:
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

    def determine_file_type(self) -> str:
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
            return result

        if "assets" in self.parts:
            result = "sub_asset"
        elif "draws" in self.parts:
            result = "sub_draw"
        elif config["DIR_JOURNALS"] in self.parts:
            result = "sub_journal"
        elif config["DIR_PAGES"] in self.parts:
            result = "sub_page"
        elif config["DIR_WHITEBOARDS"] in self.parts:
            result = "sub_whiteboard"
        return result

    @staticmethod
    def add_ordinal_suffix_to_day_of_month(day) -> str:
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return str(day) + suffix
