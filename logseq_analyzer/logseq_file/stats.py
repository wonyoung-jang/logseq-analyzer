"""
This module defines the LogseqPath class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from ..config.graph_config import get_ns_sep
from ..io.filesystem import LogseqAnalyzerDirs
from ..utils.date_utilities import DateUtilities
from ..utils.enums import Core, FileType, TargetDir
from ..utils.helpers import format_bytes

if TYPE_CHECKING:
    from ..app import ConfigEdns, JournalFormats

logger = logging.getLogger(__name__)


@dataclass
class TimestampInfo:
    """File timestamp information class."""

    time_existed: float
    time_unmodified: float
    date_created: str
    date_modified: str


@dataclass
class SizeInfo:
    """File size information class."""

    size: int
    human_readable_size: str
    has_content: bool


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
        "date",
        "file_type",
        "file",
        "is_namespace",
        "name",
        "uri",
        "logseq_url",
    )

    graph_path: Path = None
    journal_file_format: str = ""
    journal_page_format: str = ""
    journal_page_title_format: str = ""
    now_ts = datetime.now().timestamp()
    ns_file_sep: str = ""
    result_map: dict = {}
    target_dirs: dict = {}

    def __init__(self, file, dateutils: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqPath object."""
        if not isinstance(file, Path):
            raise TypeError("file must be a pathlib.Path object.")
        self.date: DateUtilities = dateutils
        self.file_type: str = ""
        self.file: Path = file
        self.is_namespace: bool = False
        self.name: str = ""
        self.uri: str = file.as_uri()
        self.logseq_url: str = ""

    def __repr__(self) -> str:
        """Return a string representation of the LogseqPath instance."""
        return f"{self.__class__.__qualname__}(file={self.file}, file_type={self.file_type})"

    def __str__(self) -> str:
        """Return a string representation of the LogseqPath instance."""
        return f"{self.__class__.__qualname__}({self.file})"

    @classmethod
    def configure(
        cls, analyzer_dirs: LogseqAnalyzerDirs, journal_formats: "JournalFormats", config_edns: "ConfigEdns"
    ) -> None:
        """Configure the LogseqPath class with necessary settings."""
        cls.graph_path = analyzer_dirs.graph_dirs.graph_dir.path
        cls.journal_file_format = journal_formats.file
        cls.journal_page_format = journal_formats.page
        cls.journal_page_title_format = journal_formats.page_title
        cls.ns_file_sep = get_ns_sep(config_edns.config)
        cls.target_dirs = analyzer_dirs.target_dirs
        cls.set_result_map()

    @classmethod
    def set_result_map(cls) -> None:
        """Set the result map for file type determination."""
        cls.result_map = {
            cls.target_dirs[TargetDir.ASSET.value]: (FileType.ASSET.value, FileType.SUB_ASSET.value),
            cls.target_dirs[TargetDir.DRAW.value]: (FileType.DRAW.value, FileType.SUB_DRAW.value),
            cls.target_dirs[TargetDir.JOURNAL.value]: (FileType.JOURNAL.value, FileType.SUB_JOURNAL.value),
            cls.target_dirs[TargetDir.PAGE.value]: (FileType.PAGE.value, FileType.SUB_PAGE.value),
            cls.target_dirs[TargetDir.WHITEBOARD.value]: (FileType.WHITEBOARD.value, FileType.SUB_WHITEBOARD.value),
        }

    def process(self) -> None:
        """Process the Logseq file path to gather statistics."""
        self.process_logseq_filename()
        self.determine_file_type()
        self.set_logseq_url()

    def set_logseq_url(self) -> None:
        """Set the Logseq URL."""
        _graph_path = LogseqPath.graph_path
        _uri = self.uri

        uri_path = Path(_uri)
        target_index = len(uri_path.parts) - len(_graph_path.parts)
        target_segment = uri_path.parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            logger.warning("Invalid target segment for Logseq URL: %s", target_segments_to_final)
            self.logseq_url = ""
            return

        graph_path = str(_graph_path).replace("\\", "/")
        prefix = f"file:///{graph_path}/{target_segment}/"
        if not _uri.startswith(prefix):
            logger.warning("URI does not start with the expected prefix: %s", prefix)
            self.logseq_url = ""
            return

        encoded_path = _uri[len(prefix) : -(len(uri_path.suffix))]
        encoded_path = encoded_path.replace("___", "%2F").replace("%253A", "%3A")
        self.logseq_url = f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"

    def determine_file_type(self, other: str = FileType.OTHER.value) -> None:
        """Helper function to determine the file type based on the directory structure."""
        _result_map = LogseqPath.result_map
        _parent = self.file.parent.name
        _parts = self.file.parts

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
        _target_dir_journal = LogseqPath.target_dirs[TargetDir.JOURNAL.value]
        _parent = self.file.parent.name
        _stem = self.file.stem

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

    def get_timestamp_info(self) -> TimestampInfo:
        """Get the timestamps for the file."""
        _now = LogseqPath.now_ts
        _stat = self.file.stat()
        _created_time = _stat.st_birthtime
        _modified_time = _stat.st_mtime
        return TimestampInfo(
            time_existed=_now - _created_time,
            time_unmodified=_now - _modified_time,
            date_created=datetime.fromtimestamp(_created_time).isoformat(),
            date_modified=datetime.fromtimestamp(_modified_time).isoformat(),
        )

    def get_size_info(self) -> SizeInfo:
        """Get the size information for the file."""
        _stat = self.file.stat()
        _size = _stat.st_size
        return SizeInfo(
            size=_size,
            human_readable_size=format_bytes(_size),
            has_content=bool(_size),
        )

    def get_namespace_info(self, ns_sep: str = Core.NS_SEP.value) -> NamespaceInfo:
        """Get the namespace name data."""
        _ns_parts_list = self.name.split(ns_sep)
        _ns_root = _ns_parts_list[0]
        return NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts_list, start=1)},
            root=_ns_root,
            parent=_ns_parts_list[-2] if len(_ns_parts_list) > 2 else _ns_root,
            parent_full=ns_sep.join(_ns_parts_list[:-1]),
            stem=_ns_parts_list[-1],
        )
