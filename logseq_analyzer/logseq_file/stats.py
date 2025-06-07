"""
This module defines the LogseqPath class, which is used to gather file statistics for Logseq files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from ..config.graph_config import get_ns_sep
from ..io.filesystem import LogseqAnalyzerDirs
from ..utils.date_utilities import DateUtilities
from ..utils.enums import Core, FileType, TargetDir
from ..utils.helpers import format_bytes
from .info import NamespaceInfo, SizeInfo, TimestampInfo, JournalFormats

if TYPE_CHECKING:
    from ..app import ConfigEdns

logger = logging.getLogger(__name__)


class LogseqFileName:
    """LogseqFileName class."""

    journal_format: JournalFormats = None
    ns_file_sep: str = ""
    journal_dir: str = ""

    @classmethod
    def configure(
        cls, analyzer_dirs: LogseqAnalyzerDirs, journal_formats: JournalFormats, config_edns: "ConfigEdns"
    ) -> None:
        """Configure the LogseqPath class with necessary settings."""
        cls.journal_format = journal_formats
        cls.ns_file_sep = get_ns_sep(config_edns.config)
        cls.journal_dir = analyzer_dirs.target_dirs[TargetDir.JOURNAL]

    @staticmethod
    def process(file: Path) -> str:
        """Process the Logseq filename based on its parent directory."""
        _ns_file_sep = LogseqFileName.ns_file_sep
        name = file.stem.strip(_ns_file_sep)

        if file.parent.name == LogseqFileName.journal_dir:
            return LogseqFileName.process_journal_key(name)
        return LogseqFileName.process_non_journal_key(name, _ns_file_sep)

    @staticmethod
    def process_journal_key(name: str, ordinal: str = Core.DATE_ORDINAL_SUFFIX) -> str:
        """Process the journal key to create a page title."""
        _file_format = LogseqFileName.journal_format.file
        _page_format = LogseqFileName.journal_format.page
        _page_title_format = LogseqFileName.journal_format.page_title

        try:
            date_obj = datetime.strptime(name, _file_format)
            page_title = date_obj.strftime(_page_format)
            if ordinal in _page_title_format:
                day_number = str(date_obj.day)
                day_with_ordinal = DateUtilities.append_ordinal_to_day(day_number)
                page_title.replace(day_number, day_with_ordinal, 1)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, _page_format, e)
            return name

    @staticmethod
    def process_non_journal_key(name: str, ns_file_sep: str, ns_sep: str = Core.NS_SEP) -> str:
        """Process non-journal keys to create a page title."""
        return unquote(name).replace(ns_file_sep, ns_sep)


class LogseqPath:
    """LogseqPath class."""

    __slots__ = (
        "file_type",
        "file",
        "logseq_url",
        "name",
        "stat",
        "uri",
    )

    graph_path: Path = None
    now_ts = datetime.now().timestamp()
    result_map: dict = {}
    target_dirs: dict = {}

    def __init__(self, file) -> None:
        """Initialize the LogseqPath object."""
        if not isinstance(file, Path):
            raise TypeError("file must be a pathlib.Path object.")
        self.file_type: str = ""
        self.file: Path = file
        self.logseq_url: str = ""
        self.name: str = ""
        self.stat = file.stat()
        self.uri: str = file.as_uri()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqPath instance."""
        return f"{self.__class__.__qualname__}(file={self.file}, file_type={self.file_type})"

    def __str__(self) -> str:
        """Return a string representation of the LogseqPath instance."""
        return f"{self.__class__.__qualname__}({self.file})"

    @classmethod
    def configure(cls, analyzer_dirs: LogseqAnalyzerDirs) -> None:
        """Configure the LogseqPath class with necessary settings."""
        cls.graph_path = analyzer_dirs.graph_dirs.graph_dir.path
        cls.target_dirs = analyzer_dirs.target_dirs
        cls.set_result_map()

    @classmethod
    def set_result_map(cls) -> None:
        """Set the result map for file type determination."""
        cls.result_map = {
            cls.target_dirs[TargetDir.ASSET]: (FileType.ASSET, FileType.SUB_ASSET),
            cls.target_dirs[TargetDir.DRAW]: (FileType.DRAW, FileType.SUB_DRAW),
            cls.target_dirs[TargetDir.JOURNAL]: (FileType.JOURNAL, FileType.SUB_JOURNAL),
            cls.target_dirs[TargetDir.PAGE]: (FileType.PAGE, FileType.SUB_PAGE),
            cls.target_dirs[TargetDir.WHITEBOARD]: (FileType.WHITEBOARD, FileType.SUB_WHITEBOARD),
        }

    def process(self) -> None:
        """Process the Logseq file path to gather statistics."""
        self.name = LogseqFileName.process(self.file)
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

    def determine_file_type(self, other: str = FileType.OTHER) -> None:
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
        _created_time = self.stat.st_birthtime
        _modified_time = self.stat.st_mtime
        return TimestampInfo(
            time_existed=_now - _created_time,
            time_unmodified=_now - _modified_time,
            date_created=datetime.fromtimestamp(_created_time).isoformat(),
            date_modified=datetime.fromtimestamp(_modified_time).isoformat(),
        )

    def get_size_info(self) -> SizeInfo:
        """Get the size information for the file."""
        _size = self.stat.st_size
        return SizeInfo(
            size=_size,
            human_readable_size=format_bytes(_size),
            has_content=bool(_size),
        )

    def get_namespace_info(self, ns_sep: str = Core.NS_SEP) -> NamespaceInfo:
        """Get the namespace name data."""
        _ns_parts_list = self.name.split(ns_sep)
        _ns_root = _ns_parts_list[0]
        return NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts_list, start=1)},
            root=_ns_root,
            parent=_ns_parts_list[-2] if len(_ns_parts_list) > 2 else _ns_root,
            parent_full=ns_sep.join(_ns_parts_list[:-1]),
            stem=_ns_parts_list[-1],
            is_namespace=Core.NS_SEP in self.name,
        )
