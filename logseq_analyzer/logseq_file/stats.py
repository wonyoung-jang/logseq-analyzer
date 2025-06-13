"""
This module defines the LogseqPath class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from os import stat_result
from pathlib import Path
from typing import ClassVar
from urllib.parse import unquote

from ..config.graph_config import ConfigEdns, get_ns_sep
from ..io.filesystem import LogseqAnalyzerDirs
from ..utils.date_utilities import DateUtilities
from ..utils.enums import Core, FileType, TargetDir
from ..utils.helpers import format_bytes
from .info import JournalFormats, NamespaceInfo, SizeInfo, TimestampInfo

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogseqFileName:
    """LogseqFileName class."""

    journal_format: ClassVar[JournalFormats] = None
    ns_file_sep: ClassVar[str] = ""
    journal_dir: ClassVar[str] = ""

    @classmethod
    def configure(
        cls, analyzer_dirs: LogseqAnalyzerDirs, journal_formats: JournalFormats, config_edns: ConfigEdns
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
    def process_journal_key(name: str) -> str:
        """Process the journal key to create a page title."""
        _file_format = LogseqFileName.journal_format.file
        _page_format = LogseqFileName.journal_format.page
        _page_title_format = LogseqFileName.journal_format.page_title

        try:
            date_obj = datetime.strptime(name, _file_format)
            page_title = date_obj.strftime(_page_format)
            if Core.DATE_ORDINAL_SUFFIX in _page_title_format:
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


@dataclass(slots=True)
class LogseqPath:
    """LogseqPath class."""

    file: Path
    file_type: str = ""
    logseq_url: str = ""
    name: str = ""
    stat: stat_result = None
    uri: str = ""

    graph_path: ClassVar[Path] = None
    now_ts: ClassVar[float] = datetime.now().timestamp()
    result_map: ClassVar[dict] = {}
    target_dirs: ClassVar[dict] = {}

    def __post_init__(self) -> None:
        """Initialize the LogseqPath object."""
        if not isinstance(self.file, Path):
            raise TypeError("file must be a pathlib.Path object.")
        self.stat = self.file.stat()
        self.uri: str = self.file.as_uri()

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
        self.file_type = self.evaluate_file_type()
        self.logseq_url = self.set_logseq_url()

    def evaluate_file_type(self) -> str:
        """Helper function to determine the file type based on the directory structure."""
        _result_map = LogseqPath.result_map
        _parent = self.file.parent.name
        _parts = self.file.parts

        result = _result_map.get(_parent, (FileType.OTHER, FileType.OTHER))

        if result[0] != FileType.OTHER:
            return result[0]

        for key, result in _result_map.items():
            if key in _parts:
                return result[1]

        return FileType.OTHER

    def set_logseq_url(self) -> str:
        """Set the Logseq URL."""
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

    def get_namespace_info(self) -> NamespaceInfo:
        """Get the namespace name data."""
        _ns_parts_list = self.name.split(Core.NS_SEP)
        _ns_root = _ns_parts_list[0]
        return NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts_list, start=1)},
            root=_ns_root,
            parent=_ns_parts_list[-2] if len(_ns_parts_list) > 2 else _ns_root,
            parent_full=Core.NS_SEP.join(_ns_parts_list[:-1]),
            stem=_ns_parts_list[-1],
            is_namespace=Core.NS_SEP in self.name,
        )
