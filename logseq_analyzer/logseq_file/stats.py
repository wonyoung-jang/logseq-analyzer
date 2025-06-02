"""
This module defines the LogseqPath class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from os import stat_result
from pathlib import Path
from urllib.parse import unquote

from ..utils.date_utilities import DateUtilities
from ..utils.enums import Core, FileTypes
from ..utils.helpers import format_bytes

logger = logging.getLogger(__name__)


@dataclass
class TimestampInfo:
    """File timestamp information class."""

    time_existed: float = 0.0
    time_unmodified: float = 0.0
    date_created: str = ""
    date_modified: str = ""


@dataclass
class SizeInfo:
    """File size information class."""

    size: int = 0
    human_readable_size: str = ""
    has_content: bool = False


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


class LogseqPath:
    """LogseqPath class."""

    __slots__ = (
        "_file",
        "date",
        "file_type",
        "name",
        "ns_info",
        "size_info",
        "stat",
        "ts_info",
        "uri",
    )

    graph_path: Path = None
    journal_file_format: str = ""
    journal_page_format: str = ""
    journal_page_title_format: str = ""
    ns_file_sep: str = ""
    target_dirs: dict = {}

    _now_ts = datetime.now().timestamp()

    def __init__(self, file: Path, dateutils: DateUtilities = DateUtilities()) -> None:
        """Initialize the LogseqPath object."""
        self.file: Path = file
        self.date: DateUtilities = dateutils
        self.file_type: str = ""
        self.name: str = ""
        self.ns_info: NamespaceInfo = None
        self.size_info: SizeInfo = None
        self.stat: stat_result = file.stat()
        self.ts_info: TimestampInfo = None
        self.uri: str = file.as_uri()

    @property
    def file(self) -> Path:
        """Return the path of the file."""
        return self._file

    @file.setter
    def file(self, value) -> None:
        """Set the path of the file."""
        if not isinstance(value, Path):
            raise TypeError("Path must be a pathlib.Path object.")
        self._file = value

    @property
    def stem(self) -> str:
        """Return the stem of the file."""
        return self.file.stem

    @property
    def parent(self) -> str:
        """Return the parent directory name."""
        return self.file.parent.name

    @property
    def parts(self) -> tuple[str, ...]:
        """Return the parts of the file path."""
        return self.file.parts

    @property
    def suffix(self) -> str:
        """Return the file extension."""
        return self.file.suffix

    @property
    def logseq_url(self) -> str:
        """Return the Logseq URL."""
        uri_path = Path(self.uri)
        target_index = len(uri_path.parts) - len(self.graph_path.parts)
        target_segment = uri_path.parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            logger.warning("Invalid target segment for Logseq URL: %s", target_segments_to_final)
            return ""
        graph_path = str(self.graph_path).replace("\\", "/")
        prefix = f"file:///{graph_path}/{target_segment}/"
        if not self.uri.startswith(prefix):
            logger.warning("URI does not start with the expected prefix: %s", prefix)
            return ""
        encoded_path = self.uri[len(prefix) : -(len(uri_path.suffix))]
        encoded_path = encoded_path.replace("___", "%2F").replace("%253A", "%3A")
        return f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"

    def process(self) -> None:
        """Process the Logseq file path to gather statistics."""
        self.process_logseq_filename()
        self.determine_file_type()
        self.set_timestamp_info()
        self.set_size_info()
        self.set_namespace_info()

    def determine_file_type(self) -> None:
        """Helper function to determine the file type based on the directory structure."""
        result = {
            LogseqPath.target_dirs["assets"]: FileTypes.ASSET.value,
            LogseqPath.target_dirs["draws"]: FileTypes.DRAW.value,
            LogseqPath.target_dirs["journals"]: FileTypes.JOURNAL.value,
            LogseqPath.target_dirs["pages"]: FileTypes.PAGE.value,
            LogseqPath.target_dirs["whiteboards"]: FileTypes.WHITEBOARD.value,
        }.get(self.parent, FileTypes.OTHER.value)
        if result != FileTypes.OTHER.value:
            self.file_type = result
        else:
            result_map = {
                LogseqPath.target_dirs["assets"]: FileTypes.SUB_ASSET.value,
                LogseqPath.target_dirs["draws"]: FileTypes.SUB_DRAW.value,
                LogseqPath.target_dirs["journals"]: FileTypes.SUB_JOURNAL.value,
                LogseqPath.target_dirs["pages"]: FileTypes.SUB_PAGE.value,
                LogseqPath.target_dirs["whiteboards"]: FileTypes.SUB_WHITEBOARD.value,
            }
            for key, value in result_map.items():
                if key in self.parts:
                    self.file_type = value
                    break

    def process_logseq_filename(self) -> None:
        """Process the Logseq filename based on its parent directory."""
        name = self.stem.strip(LogseqPath.ns_file_sep)

        if self.parent == LogseqPath.target_dirs["journals"]:
            self.name = self._process_logseq_journal_key(name)
        else:
            self.name = self._process_logseq_non_journal_key(name)

    def _process_logseq_non_journal_key(self, name: str) -> str:
        """Process non-journal keys to create a page title."""
        return unquote(name).replace(LogseqPath.ns_file_sep, Core.NS_SEP.value)

    def _process_logseq_journal_key(self, name: str) -> str:
        """Process the journal key to create a page title."""
        try:
            name = datetime.strptime(name, LogseqPath.journal_file_format)
            page_title = name.strftime(LogseqPath.journal_page_format)
            if Core.DATE_ORDINAL_SUFFIX.value in LogseqPath.journal_page_title_format:
                page_title = self._get_ordinal_day(name, page_title)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, LogseqPath.journal_page_format, e)
            return name

    def _get_ordinal_day(self, date_object: datetime, page_title: str) -> str:
        """Get the ordinal day from the date object and page title."""
        day_number = str(date_object.day)
        day_with_ordinal = self.date.append_ordinal_to_day(day_number)
        return page_title.replace(day_number, day_with_ordinal, 1)

    def read_text(self) -> str:
        """Read the text content of a file."""
        try:
            return self.file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Failed to decode file %s with utf-8 encoding.", self.file)
        return ""

    def set_timestamp_info(self) -> None:
        """Set the timestamps for the file."""
        self.ts_info = TimestampInfo()
        self.ts_info.time_existed = self._now_ts - self.stat.st_birthtime
        self.ts_info.time_unmodified = self._now_ts - self.stat.st_mtime
        self.ts_info.date_created = datetime.fromtimestamp(self.stat.st_birthtime).isoformat()
        self.ts_info.date_modified = datetime.fromtimestamp(self.stat.st_mtime).isoformat()

    def set_size_info(self) -> None:
        """Set the size information for the file."""
        self.size_info = SizeInfo()
        self.size_info.size = self.stat.st_size
        self.size_info.human_readable_size = format_bytes(self.size_info.size)
        self.size_info.has_content = bool(self.size_info.size)

    def set_namespace_info(self) -> None:
        """Get the namespace name data."""
        ns_parts_list = self.name.split(Core.NS_SEP.value)
        ns_root = ns_parts_list[0]
        self.ns_info = NamespaceInfo()
        self.ns_info.parts = {part: level for level, part in enumerate(ns_parts_list, start=1)}
        self.ns_info.root = ns_root
        self.ns_info.parent = ns_parts_list[-2] if len(ns_parts_list) > 2 else ns_root
        self.ns_info.parent_full = Core.NS_SEP.value.join(ns_parts_list[:-1])
        self.ns_info.stem = ns_parts_list[-1]
