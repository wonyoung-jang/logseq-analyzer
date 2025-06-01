"""
This module handles processing of Logseq filenames based on their parent directory.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from ..utils.date_utilities import DateUtilities
from ..utils.enums import Core, FileTypes

logger = logging.getLogger(__name__)


@dataclass
class NamespaceInfo:
    """NamespaceInfo class."""

    children: set[str] = field(default_factory=set)
    parent_full: str = ""
    parent: str = ""
    parts: dict[str, int] = field(default_factory=dict)
    root: str = ""
    size: int = 0
    stem: str = ""


class LogseqFilename:
    """LogseqFilename class."""

    graph_path: Path = None
    journal_file_format: str = ""
    journal_page_format: str = ""
    journal_page_title_format: str = ""
    ns_file_sep: str = ""
    target_dirs: dict = {}

    __slots__ = (
        "_is_namespace",
        "date",
        "path",
        "file_type",
        "name",
        "ns_info",
    )

    def __init__(self, path: Path, date_utilities: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqFilename class."""
        self.date: DateUtilities = date_utilities
        self.path: Path = path
        self.file_type: str = ""
        self.name: str = path.stem
        self.ns_info: NamespaceInfo = NamespaceInfo()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqFilename object."""
        return f"{self.__class__.__qualname__}({self.path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqFilename object."""
        return f"{self.__class__.__qualname__}: {self.path}"

    @property
    def is_hls(self) -> bool:
        """Check if the filename is a HLS."""
        return self.name.startswith(Core.HLS_PREFIX.value)

    @property
    def is_namespace(self) -> bool:
        """Check if the filename is a namespace."""
        self._is_namespace = Core.NS_SEP.value in self.name
        return self._is_namespace

    @is_namespace.setter
    def is_namespace(self, value: Any) -> None:
        """Set the is_namespace property."""
        if not isinstance(value, bool):
            raise ValueError("is_namespace must be a boolean value.")
        self._is_namespace = value

    @property
    def uri(self) -> str:
        """Return the file URI."""
        return self.path.as_uri()

    @property
    def logseq_url(self) -> str:
        """Return the Logseq URL."""
        uri_path = Path(self.uri)
        target_index = len(uri_path.parts) - len(self.graph_path.parts)
        target_segment = uri_path.parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            return ""
        prefix = f"file:///{str(self.graph_path)}/{target_segment}/"
        if not self.uri.startswith(prefix):
            return ""
        encoded_path = self.uri[len(prefix) : -(len(uri_path.suffix))]
        encoded_path = encoded_path.replace("___", "%2F").replace("%253A", "%3A")
        return f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"

    def process(self, ns_sep: str = Core.NS_SEP.value, ordinal_suffix: str = Core.DATE_ORDINAL_SUFFIX.value) -> None:
        """Process the filename based on its parent directory."""
        self.file_type = self.determine_file_type()
        self.name = self.process_logseq_filename(ns_sep, ordinal_suffix)
        self.get_namespace_name_data(ns_sep)

    def determine_file_type(self) -> str:
        """
        Helper function to determine the file type based on the directory structure.
        """
        result = {
            self.target_dirs["assets"]: FileTypes.ASSET.value,
            self.target_dirs["draws"]: FileTypes.DRAW.value,
            self.target_dirs["journals"]: FileTypes.JOURNAL.value,
            self.target_dirs["pages"]: FileTypes.PAGE.value,
            self.target_dirs["whiteboards"]: FileTypes.WHITEBOARD.value,
        }.get(self.path.parent.name, FileTypes.OTHER.value)

        if result != FileTypes.OTHER.value:
            return result

        result_map = {
            self.target_dirs["assets"]: FileTypes.SUB_ASSET.value,
            self.target_dirs["draws"]: FileTypes.SUB_DRAW.value,
            self.target_dirs["journals"]: FileTypes.SUB_JOURNAL.value,
            self.target_dirs["pages"]: FileTypes.SUB_PAGE.value,
            self.target_dirs["whiteboards"]: FileTypes.SUB_WHITEBOARD.value,
        }
        for key, value in result_map.items():
            if key in self.path.parts:
                result = value
                break
        return result

    def process_logseq_filename(
        self, ns_sep: str = Core.NS_SEP.value, ordinal_suffix: str = Core.DATE_ORDINAL_SUFFIX.value
    ) -> str:
        """Process the Logseq filename based on its parent directory."""
        name = self.name.strip(self.ns_file_sep)
        if self.path.parent.name == self.target_dirs["journals"]:
            return self.process_logseq_journal_key(name, ordinal_suffix)
        return unquote(name).replace(self.ns_file_sep, ns_sep)

    def process_logseq_journal_key(self, name: str, ordinal_suffix: str = Core.DATE_ORDINAL_SUFFIX.value) -> str:
        """Process the journal key to create a page title."""
        try:
            date_object = datetime.strptime(name, self.journal_file_format)
            page_title = date_object.strftime(self.journal_page_format)
            if ordinal_suffix in self.journal_page_title_format:
                page_title = self.get_ordinal_day(date_object, page_title)
            page_title = page_title.replace("'", "")
            return page_title
        except ValueError as e:
            logger.warning("Failed to parse date from key '%s', format `%s`: %s", name, self.journal_page_format, e)
            return ""

    def get_ordinal_day(self, date_object: datetime, page_title: str) -> str:
        """Get the ordinal day from the date object and page title."""
        day_number = str(date_object.day)
        day_with_ordinal = self.date.append_ordinal_to_day(day_number)
        return page_title.replace(day_number, day_with_ordinal, 1)

    def get_namespace_name_data(self, ns_sep: str = Core.NS_SEP.value) -> None:
        """Get the namespace name data."""
        if not self.is_namespace:
            return
        ns_parts_list = self.name.split(ns_sep)
        ns_root = ns_parts_list[0]
        self.ns_info.parts = {part: level for level, part in enumerate(ns_parts_list, start=1)}
        self.ns_info.root = ns_root
        self.ns_info.parent = ns_parts_list[-2] if len(ns_parts_list) > 2 else ns_root
        self.ns_info.parent_full = ns_sep.join(ns_parts_list[:-1])
        self.ns_info.stem = ns_parts_list[-1]
