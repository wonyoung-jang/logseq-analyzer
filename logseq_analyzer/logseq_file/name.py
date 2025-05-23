"""
This module handles processing of Logseq filenames based on their parent directory.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from ..io.filesystem import GraphDirectory
from ..utils.enums import Core, FileTypes, Config


@dataclass
class NamespaceInfo:
    """NamespaceInfo class."""

    parts: dict[str, int] = field(default_factory=dict)
    root: str = ""
    parent: str = ""
    parent_full: str = ""
    stem: str = ""
    children: set[str] = field(default_factory=set)
    size: int = 0


class LogseqFilename:
    """LogseqFilename class."""

    __slots__ = (
        "file_path",
        "name",
        "file_type",
        "is_hls",
        "is_namespace",
        "ns_info",
    )

    gc_config: dict = {}
    journal_file_format: str = ""
    journal_page_format: str = ""
    lac_ls_config: dict = {}
    ns_file_sep: str = ""

    def __init__(self, file_path: Path) -> None:
        """Initialize the LogseqFilename class."""
        self.file_path: Path = file_path
        self.name: str = file_path.stem
        self.file_type: str = ""
        self.is_hls: bool = False
        self.is_namespace: bool = False
        self.ns_info: NamespaceInfo = NamespaceInfo()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqFilename object."""
        return f"{self.__class__.__qualname__}({self.file_path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqFilename object."""
        return f"{self.__class__.__qualname__}: {self.file_path}"

    @property
    def parent(self) -> str:
        """Return the parent directory of the file."""
        return self.file_path.parent.name

    @property
    def suffix(self) -> str:
        """Return the file extension."""
        return self.file_path.suffix if self.file_path.suffix else ""

    @property
    def parts(self) -> tuple[str, ...]:
        """Return the parts of the file path."""
        return self.file_path.parts

    @property
    def uri(self) -> str:
        """Return the file URI."""
        return self.file_path.as_uri()

    @property
    def logseq_url(self) -> str:
        """Return the Logseq URL."""
        uri = self.uri
        uri_path = Path(uri)
        gd = GraphDirectory()
        len_gd = len(gd.path.parts)
        len_uri = len(uri_path.parts)
        target_index = len_uri - len_gd
        target_segment = uri_path.parts[target_index]
        if target_segment[:-1] not in ("page", "block-id"):
            return ""

        prefix = f"file:///{str(gd.path)}/{target_segment}/"
        if not uri.startswith(prefix):
            return ""

        len_suffix = len(uri_path.suffix)
        path_without_prefix = uri[len(prefix) : -(len_suffix)]
        path_with_slashes = path_without_prefix.replace("___", "%2F").replace("%253A", "%3A")
        encoded_path = path_with_slashes
        target_segment = target_segment[:-1]
        return f"logseq://graph/Logseq?{target_segment}={encoded_path}"

    def process_filename(self) -> None:
        """Process the filename based on its parent directory."""
        self.determine_file_type()
        self.process_logseq_filename()
        self.check_is_hls()
        self.check_is_namespace()
        if self.is_namespace:
            self.get_namespace_name_data()

    def process_logseq_filename(self) -> None:
        """Process the Logseq filename based on its parent directory."""
        ns_file_sep = LogseqFilename.ns_file_sep
        lac_ls_config = LogseqFilename.lac_ls_config
        name = self.name.strip(ns_file_sep)
        if self.parent == lac_ls_config["DIR_JOURNALS"]:
            self.name = self.process_logseq_journal_key(name)
        else:
            self.name = unquote(name).replace(ns_file_sep, Core.NS_SEP.value)

    def check_is_hls(self) -> None:
        """Check if the filename is a HLS."""
        self.is_hls = self.name.startswith(Core.HLS_PREFIX.value)

    def check_is_namespace(self) -> None:
        """Check if the filename is a namespace."""
        self.is_namespace = Core.NS_SEP.value in self.name

    def get_namespace_name_data(self) -> None:
        """Get the namespace name data."""
        ns_parts_list = self.name.split(Core.NS_SEP.value)
        ns_root = ns_parts_list[0]
        self.ns_info.parts = {part: level for level, part in enumerate(ns_parts_list, start=1)}
        self.ns_info.root = ns_root
        self.ns_info.parent = ns_parts_list[-2] if len(ns_parts_list) > 2 else ns_root
        self.ns_info.parent_full = Core.NS_SEP.value.join(ns_parts_list[:-1])
        self.ns_info.stem = ns_parts_list[-1]
        self.ns_info.children = set()
        self.ns_info.size = 0

    def determine_file_type(self) -> None:
        """
        Helper function to determine the file type based on the directory structure.
        """
        config = LogseqFilename.lac_ls_config
        result = {
            config[Config.DIR_ASSETS.value]: FileTypes.ASSET.value,
            config[Config.DIR_DRAWS.value]: FileTypes.DRAW.value,
            config[Config.DIR_JOURNALS.value]: FileTypes.JOURNAL.value,
            config[Config.DIR_PAGES.value]: FileTypes.PAGE.value,
            config[Config.DIR_WHITEBOARDS.value]: FileTypes.WHITEBOARD.value,
        }.get(self.parent, FileTypes.OTHER.value)

        if result != FileTypes.OTHER.value:
            self.file_type = result
        else:
            parts = self.parts
            if config[Config.DIR_ASSETS.value] in parts:
                result = FileTypes.SUB_ASSET.value
            elif config[Config.DIR_DRAWS.value] in parts:
                result = FileTypes.SUB_DRAW.value
            elif config[Config.DIR_JOURNALS.value] in parts:
                result = FileTypes.SUB_JOURNAL.value
            elif config[Config.DIR_PAGES.value] in parts:
                result = FileTypes.SUB_PAGE.value
            elif config[Config.DIR_WHITEBOARDS.value] in parts:
                result = FileTypes.SUB_WHITEBOARD.value
            self.file_type = result

    @classmethod
    def process_logseq_journal_key(cls, name: str) -> str:
        """Process the journal key to create a page title."""
        try:
            file_format = cls.journal_file_format
            page_format = cls.journal_page_format
            gc_config = cls.gc_config
            date_object = datetime.strptime(name, file_format)
            page_title_base = date_object.strftime(page_format)
            if Core.DATE_ORDINAL_SUFFIX.value in gc_config.get(":journal/page-title-format"):
                day_number = date_object.day
                day_with_ordinal = LogseqFilename.add_ordinal_suffix_to_day_of_month(day_number)
                page_title = page_title_base.replace(str(day_number), day_with_ordinal, 1)
            else:
                page_title = page_title_base
            page_title = page_title.replace("'", "")
            return page_title
        except ValueError as e:
            logging.warning("Failed to parse date from key '%s', format `%s`: %s", name, page_format, e)
            return ""

    @staticmethod
    def add_ordinal_suffix_to_day_of_month(day) -> str:
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        if 11 <= day <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return str(day) + suffix
