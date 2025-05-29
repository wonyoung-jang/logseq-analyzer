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
        "file_path",
        "file_type",
        "name",
        "ns_info",
    )

    def __init__(self, file_path: Path, date_utilities: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqFilename class."""
        self.date: DateUtilities = date_utilities
        self.file_path: Path = file_path
        self.file_type: str = ""
        self.name: str = file_path.stem
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
        graph_path = LogseqFilename.graph_path
        uri_path_parts = uri_path.parts
        graph_path_parts = graph_path.parts
        target_index = len(uri_path_parts) - len(graph_path_parts)
        target_segment = uri_path_parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            return ""

        prefix = f"file:///{str(graph_path)}/{target_segment}/"
        if not uri.startswith(prefix):
            return ""

        suffix = uri_path.suffix
        encoded_path = uri[len(prefix) : -(len(suffix))]
        encoded_path = encoded_path.replace("___", "%2F").replace("%253A", "%3A")
        return f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"

    def process_filename(self) -> None:
        """Process the filename based on its parent directory."""
        self.determine_file_type()
        self.process_logseq_filename()
        self.get_namespace_name_data()

    def process_logseq_filename(self) -> None:
        """Process the Logseq filename based on its parent directory."""
        ns_file_sep = LogseqFilename.ns_file_sep
        target_dirs = LogseqFilename.target_dirs
        name = self.name.strip(ns_file_sep)
        if self.parent == target_dirs["journals"]:
            self.name = self.process_logseq_journal_key(name)
        else:
            self.name = unquote(name).replace(ns_file_sep, Core.NS_SEP.value)

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

    def get_namespace_name_data(self) -> None:
        """Get the namespace name data."""
        if not self.is_namespace:
            return
        ns_parts_list = self.name.split(Core.NS_SEP.value)
        ns_root = ns_parts_list[0]
        self.ns_info.parts = {part: level for level, part in enumerate(ns_parts_list, start=1)}
        self.ns_info.root = ns_root
        self.ns_info.parent = ns_parts_list[-2] if len(ns_parts_list) > 2 else ns_root
        self.ns_info.parent_full = Core.NS_SEP.value.join(ns_parts_list[:-1])
        self.ns_info.stem = ns_parts_list[-1]

    def determine_file_type(self) -> None:
        """
        Helper function to determine the file type based on the directory structure.
        """
        target_dirs = LogseqFilename.target_dirs
        result = {
            target_dirs["assets"]: FileTypes.ASSET.value,
            target_dirs["draws"]: FileTypes.DRAW.value,
            target_dirs["journals"]: FileTypes.JOURNAL.value,
            target_dirs["pages"]: FileTypes.PAGE.value,
            target_dirs["whiteboards"]: FileTypes.WHITEBOARD.value,
        }.get(self.parent, FileTypes.OTHER.value)

        if result != FileTypes.OTHER.value:
            self.file_type = result
        else:
            parts = self.parts
            result_map = {
                target_dirs["assets"]: FileTypes.SUB_ASSET.value,
                target_dirs["draws"]: FileTypes.SUB_DRAW.value,
                target_dirs["journals"]: FileTypes.SUB_JOURNAL.value,
                target_dirs["pages"]: FileTypes.SUB_PAGE.value,
                target_dirs["whiteboards"]: FileTypes.SUB_WHITEBOARD.value,
            }
            for key, result in result_map.items():
                if key in parts:
                    self.file_type = result
                    break

    def process_logseq_journal_key(self, name: str) -> str:
        """Process the journal key to create a page title."""
        try:
            file_format = LogseqFilename.journal_file_format
            page_format = LogseqFilename.journal_page_format
            journal_page_title_format = LogseqFilename.journal_page_title_format
            date_object = datetime.strptime(name, file_format)
            page_title = date_object.strftime(page_format)
            if Core.DATE_ORDINAL_SUFFIX.value in journal_page_title_format:
                day_number = str(date_object.day)
                day_with_ordinal = self.date.append_ordinal_to_day(day_number)
                page_title = page_title.replace(day_number, day_with_ordinal, 1)
            page_title = page_title.replace("'", "")
            return page_title
        except ValueError as e:
            logger.warning("Failed to parse date from key '%s', format `%s`: %s", name, page_format, e)
            return ""
