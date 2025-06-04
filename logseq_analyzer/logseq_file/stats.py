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
        "is_namespace",
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
        self.is_namespace: bool = False

    def __repr__(self) -> str:
        """Return a string representation of the LogseqPath instance."""
        return f"{self.__class__.__qualname__}(file={self.file}, file_type={self.file_type})"

    def __str__(self) -> str:
        """Return a string representation of the LogseqPath instance."""
        return f"{self.__class__.__qualname__}({self.file})"

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

    def determine_file_type(self, other: str = FileTypes.OTHER.value) -> None:
        """Helper function to determine the file type based on the directory structure."""
        _result_map = LogseqPath.result_map
        _parent = self.parent
        _parts = self.parts

        result = _result_map.get(_parent, (other, other))

        if result[0] != other:
            self.file_type = result[0]
            return

        for key, result in _result_map.items():
            if key in _parts:
                self.file_type = result[1]
                return

    def process_logseq_filename(self, ns_sep: str = Core.NS_SEP.value) -> None:
        """Process the Logseq filename based on its parent directory."""
        _ns_file_sep = LogseqPath.ns_file_sep
        _target_dir_journal = LogseqPath.target_dirs["journals"]
        _parent = self.parent
        _stem = self.stem

        if _parent == _target_dir_journal:
            self.name = self._process_logseq_journal_key(_stem.strip(_ns_file_sep))
        else:
            self.name = self._process_logseq_non_journal_key(_stem.strip(_ns_file_sep), _ns_file_sep)

        self.is_namespace = ns_sep in self.name

    def _process_logseq_non_journal_key(self, name: str, ns_file_sep: str, ns_sep: str = Core.NS_SEP.value) -> str:
        """Process non-journal keys to create a page title."""
        return unquote(name).replace(ns_file_sep, ns_sep)

    def _process_logseq_journal_key(self, name: str, ordinal: str = Core.DATE_ORDINAL_SUFFIX.value) -> str:
        """Process the journal key to create a page title."""
        _file_format = LogseqPath.journal_file_format
        _page_format = LogseqPath.journal_page_format
        _page_title_format = LogseqPath.journal_page_title_format

        try:
            date_obj = datetime.strptime(name, _file_format)
            page_title = date_obj.strftime(_page_format)
            if ordinal in _page_title_format:
                page_title = self._get_ordinal_day(date_obj, page_title)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, _page_format, e)
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
        self.ts_info = TimestampInfo(
            time_existed=_now - _created_time,
            time_unmodified=_now - _modified_time,
            date_created=datetime.fromtimestamp(_created_time).isoformat(),
            date_modified=datetime.fromtimestamp(_modified_time).isoformat(),
        )

    def set_size_info(self) -> None:
        """Set the size information for the file."""
        _size = self.stat.st_size
        self.size_info = SizeInfo(
            size=_size,
            human_readable_size=format_bytes(_size),
            has_content=bool(_size),
        )

    def set_namespace_info(self, ns_sep: str = Core.NS_SEP.value) -> None:
        """Get the namespace name data."""
        _ns_parts_list = self.name.split(ns_sep)
        _ns_root = _ns_parts_list[0]
        self.ns_info = NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts_list, start=1)},
            root=_ns_root,
            parent=_ns_parts_list[-2] if len(_ns_parts_list) > 2 else _ns_root,
            parent_full=ns_sep.join(_ns_parts_list[:-1]),
            stem=_ns_parts_list[-1],
        )
