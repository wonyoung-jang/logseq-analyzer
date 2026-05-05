"""Module defining the LogseqPath class, which is used to gather file statistics for Logseq files."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import unquote

from logseq_analyzer.config.graph_config import ConfigEdns, get_ns_sep
from logseq_analyzer.logseq_file.info import JournalFormats, NamespaceInfo, SizeInfo, TimestampInfo
from logseq_analyzer.utils.date_utilities import DateUtilities
from logseq_analyzer.utils.enums import Core, FileType, TargetDir
from logseq_analyzer.utils.helpers import format_bytes

if TYPE_CHECKING:
    from os import stat_result

    from logseq_analyzer.io.filesystem import LogseqAnalyzerDirs

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogseqFileName:
    """LogseqFileName class."""

    journal_format: ClassVar[JournalFormats]
    ns_file_sep: ClassVar[str]
    journal_dir: ClassVar[str]

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
        name = file.stem.strip(LogseqFileName.ns_file_sep)
        if file.parent.name == LogseqFileName.journal_dir:
            return LogseqFileName.process_journal_key(name)
        return LogseqFileName.process_non_journal_key(name, LogseqFileName.ns_file_sep)

    @staticmethod
    def process_journal_key(name: str) -> str:
        """Process the journal key to create a page title."""
        try:
            date_obj = datetime.strptime(name, LogseqFileName.journal_format.file).replace(tzinfo=UTC)
            page_title = date_obj.strftime(LogseqFileName.journal_format.page)
            if Core.DATE_ORDINAL_SUFFIX in LogseqFileName.journal_format.page_title:
                day_number = str(date_obj.day)
                day_with_ordinal = DateUtilities.append_ordinal_to_day(day_number)
                page_title.replace(day_number, day_with_ordinal, 1)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, LogseqFileName.journal_format.page, e)
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
    stat: stat_result = field(init=False)
    uri: str = ""
    now_ts: ClassVar[float] = datetime.now(tz=UTC).timestamp()
    graph_path: ClassVar[Path]
    result_map: ClassVar[dict]
    target_dirs: ClassVar[dict]

    def __post_init__(self) -> None:
        """Initialize the LogseqPath object."""
        if not isinstance(self.file, Path):
            msg = "file must be a pathlib.Path object."
            raise TypeError(msg)
        self.stat = self.file.stat()
        self.uri: str = self.file.as_uri()

    @classmethod
    def configure(cls, analyzer_dirs: LogseqAnalyzerDirs) -> None:
        """Configure the LogseqPath class with necessary settings."""
        cls.graph_path = analyzer_dirs.graph_dirs.graph_dir.path
        cls.target_dirs = analyzer_dirs.target_dirs
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
        """Determine the file type based on the directory structure."""
        _result = LogseqPath.result_map.get(self.file.parent.name, (FileType.OTHER, FileType.OTHER))
        if _result[0] != FileType.OTHER:
            return _result[0]
        for key, _result in LogseqPath.result_map.items():
            if key in self.file.parts:
                return _result[1]
        return FileType.OTHER

    def set_logseq_url(self) -> str:
        """Set the Logseq URL."""
        uri_path = Path(self.uri)
        target_index = len(uri_path.parts) - len(LogseqPath.graph_path.parts)
        target_segment = uri_path.parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            logger.warning("Invalid target segment for Logseq URL: %s", target_segments_to_final)
            return ""
        graph_path = str(LogseqPath.graph_path).replace("\\", "/")
        prefix = f"file:///{graph_path}/{target_segment}/"
        if not self.uri.startswith(prefix):
            logger.warning("URI does not start with the expected prefix: %s", prefix)
            return ""
        encoded_path = self.uri[len(prefix) : -(len(uri_path.suffix))]
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
        return TimestampInfo(
            time_existed=LogseqPath.now_ts - self.stat.st_birthtime,
            time_unmodified=LogseqPath.now_ts - self.stat.st_mtime,
            date_created=datetime.fromtimestamp(self.stat.st_birthtime, tz=UTC).isoformat(),
            date_modified=datetime.fromtimestamp(self.stat.st_mtime, tz=UTC).isoformat(),
        )

    def get_size_info(self) -> SizeInfo:
        """Get the size information for the file."""
        return SizeInfo(
            size=self.stat.st_size,
            human_readable_size=format_bytes(self.stat.st_size),
            has_content=bool(self.stat.st_size),
        )

    def get_namespace_info(self) -> NamespaceInfo:
        """Get the namespace name data."""
        _ns_parts_list = self.name.split(Core.NS_SEP)
        return NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts_list, start=1)},
            root=_ns_parts_list[0],
            parent=_ns_parts_list[-2] if len(_ns_parts_list) > 2 else _ns_parts_list[0],
            parent_full=Core.NS_SEP.join(_ns_parts_list[:-1]),
            stem=_ns_parts_list[-1],
            is_namespace=Core.NS_SEP in self.name,
        )
