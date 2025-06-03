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
        "file",
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
    result_map: dict = None
    now_ts = datetime.now().timestamp()

    def __init__(self, file, dateutils: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqPath object."""
        if not isinstance(file, Path):
            raise TypeError("file must be a pathlib.Path object.")
        self.file: Path = file
        self.stat: stat_result = file.stat()
        self.uri: str = file.as_uri()
        self.file_type: str = ""
        self.name: str = ""
        self.date: DateUtilities = dateutils
        self.ns_info: NamespaceInfo = None
        self.size_info: SizeInfo = None
        self.ts_info: TimestampInfo = None

    @classmethod
    def set_result_map(cls) -> None:
        """Set the result map for file type determination."""
        _target_dirs = cls.target_dirs
        cls.result_map = {
            _target_dirs["assets"]: (FileTypes.ASSET.value, FileTypes.SUB_ASSET.value),
            _target_dirs["draws"]: (FileTypes.DRAW.value, FileTypes.SUB_DRAW.value),
            _target_dirs["journals"]: (FileTypes.JOURNAL.value, FileTypes.SUB_JOURNAL.value),
            _target_dirs["pages"]: (FileTypes.PAGE.value, FileTypes.SUB_PAGE.value),
            _target_dirs["whiteboards"]: (FileTypes.WHITEBOARD.value, FileTypes.SUB_WHITEBOARD.value),
        }

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
        _graph_path = LogseqPath.graph_path
        _uri = self.uri

        uri_path = Path(_uri)
        target_index = len(uri_path.parts) - len(_graph_path.parts)
        target_segment = uri_path.parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            logger.warning("Invalid target segment for Logseq URL: %s", target_segments_to_final)
            return ""

        graph_path = str(_graph_path).replace("\\", "/")
        prefix = f"file:///{graph_path}/{target_segment}/"
        if not _uri.startswith(prefix):
            logger.warning("URI does not start with the expected prefix: %s", prefix)
            return ""

        encoded_path = _uri[len(prefix) : -(len(uri_path.suffix))]
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
        _result_map = LogseqPath.result_map
        _parent = self.parent
        _parts = self.parts

        result = _result_map.get(_parent, (FileTypes.OTHER.value, FileTypes.OTHER.value))

        if result[0] != FileTypes.OTHER.value:
            self.file_type = result[0]
            return

        for key, result in _result_map.items():
            if key in _parts:
                self.file_type = result[1]
                return

    def process_logseq_filename(self) -> None:
        """Process the Logseq filename based on its parent directory."""
        _ns_file_sep = LogseqPath.ns_file_sep
        _target_dir_journal = LogseqPath.target_dirs["journals"]
        _parent = self.parent
        _stem = self.stem

        if _parent == _target_dir_journal:
            self.name = self._process_logseq_journal_key(_stem.strip(_ns_file_sep))
        else:
            self.name = self._process_logseq_non_journal_key(_stem.strip(_ns_file_sep), _ns_file_sep)

    def _process_logseq_non_journal_key(self, name: str, ns_file_sep: str) -> str:
        """Process non-journal keys to create a page title."""
        return unquote(name).replace(ns_file_sep, Core.NS_SEP.value)

    def _process_logseq_journal_key(self, name: str) -> str:
        """Process the journal key to create a page title."""
        _journal_file_format = LogseqPath.journal_file_format
        _journal_page_format = LogseqPath.journal_page_format
        _journal_page_title_format = LogseqPath.journal_page_title_format

        try:
            date_obj = datetime.strptime(name, _journal_file_format)
            page_title = date_obj.strftime(_journal_page_format)
            if Core.DATE_ORDINAL_SUFFIX.value in _journal_page_title_format:
                page_title = self._get_ordinal_day(date_obj, page_title)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, _journal_page_format, e)
            return name

    def _get_ordinal_day(self, date_obj: datetime, page_title: str) -> str:
        """Get the ordinal day from the date object and page title."""
        day_number = str(date_obj.day)
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
        _now = LogseqPath.now_ts
        _created_time = self.stat.st_birthtime
        _modified_time = self.stat.st_mtime

        _ts_info = TimestampInfo()
        _ts_info.time_existed = _now - _created_time
        _ts_info.time_unmodified = _now - _modified_time
        _ts_info.date_created = datetime.fromtimestamp(_created_time).isoformat()
        _ts_info.date_modified = datetime.fromtimestamp(_modified_time).isoformat()

        self.ts_info = _ts_info

    def set_size_info(self) -> None:
        """Set the size information for the file."""
        _size = self.stat.st_size

        _size_info = SizeInfo()
        _size_info.size = _size
        _size_info.human_readable_size = format_bytes(_size)
        _size_info.has_content = bool(_size)

        self.size_info = _size_info

    def set_namespace_info(self) -> None:
        """Get the namespace name data."""
        _ns_sep = Core.NS_SEP.value
        _ns_parts_list = self.name.split(_ns_sep)
        _ns_root = _ns_parts_list[0]

        _ns_info = NamespaceInfo()
        _ns_info.parts = {part: level for level, part in enumerate(_ns_parts_list, start=1)}
        _ns_info.root = _ns_root
        _ns_info.parent = _ns_parts_list[-2] if len(_ns_parts_list) > 2 else _ns_root
        _ns_info.parent_full = _ns_sep.join(_ns_parts_list[:-1])
        _ns_info.stem = _ns_parts_list[-1]

        self.ns_info = _ns_info
