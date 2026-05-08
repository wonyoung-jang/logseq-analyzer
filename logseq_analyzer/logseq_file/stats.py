"""Module defining the LogseqPath class, which is used to gather file statistics for Logseq files."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from logseq_analyzer.logseq_file.info import JournalFormats, NamespaceInfo, SizeInfo, TimestampInfo
from logseq_analyzer.utils.enums import Core, FileType

if TYPE_CHECKING:
    from os import stat_result

    from logseq_analyzer.logseq_file.file import LogseqFileContext

logger = logging.getLogger(__name__)

SI_UNITS = ["B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
IEC_UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]


class SizeUnit(StrEnum):
    """Enumeration for size units."""

    SI = "si"  # Powers of 1000
    IEC = "iec"  # Powers of 1024


_ORDINAL_SUFFIX = {1: "st", 2: "nd", 3: "rd"}


def append_ordinal_to_day(day: str) -> str:
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    day_int = int(day)
    if 11 <= day_int <= 13:
        return day + "th"
    return day + _ORDINAL_SUFFIX.get(day_int % 10, "th")


def _get_non_journal_key(name: str, ns_file_sep: str) -> str:
    """Process non-journal keys to create a page title."""
    return unquote(name).replace(ns_file_sep, Core.NS_SEP)


def _get_journal_key(name: str, file_fmt: str, page_fmt: str, page_title_fmt: str) -> str:
    """Process the journal key to create a page title."""
    try:
        date_obj = datetime.strptime(name, file_fmt).replace(tzinfo=UTC)
        page_title = date_obj.strftime(page_fmt)
        if Core.DATE_ORDINAL_SUFFIX in page_title_fmt:
            day_number = str(date_obj.day)
            day_with_ordinal = append_ordinal_to_day(day_number)
            page_title = page_title.replace(day_number, day_with_ordinal, 1)
        return page_title.replace("'", "")
    except ValueError as e:
        logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, page_fmt, e)
        return name


@dataclass(slots=True)
class LogseqFileName:
    """LogseqFileName class."""

    journal_format: JournalFormats
    ns_file_sep: str
    journal_dir: str

    def __call__(self, file: Path) -> str:
        """Process the Logseq filename based on its parent directory."""
        name = file.stem.strip(self.ns_file_sep)
        if file.parent.name == self.journal_dir:
            return _get_journal_key(
                name,
                self.journal_format.file,
                self.journal_format.page,
                self.journal_format.page_title,
            )
        return _get_non_journal_key(name, self.ns_file_sep)


def format_bytes(size_bytes: int, system: str = SizeUnit.SI, precision: int = 2) -> str:
    """Convert a byte value into a human-readable string using SI or IEC units.

    Args:
        size_bytes (int): Number of bytes.
        system (str): 'si' for powers of 1000, 'iec' for powers of 1024.
        precision (int): Number of decimal places.

    Returns:
        str: Human-readable string, e.g. '1.23 MB' or '1.20 MiB'.

    """
    if size_bytes < 0:
        msg = "size_bytes must be non-negative"
        raise ValueError(msg)
    units = IEC_UNITS if system == SizeUnit.IEC else SI_UNITS
    base = 1024 if system == SizeUnit.IEC else 1000
    if size_bytes < base:
        return f"{size_bytes} {units[0]}"
    idx = 0
    size = float(size_bytes)
    while size >= base and idx < len(units) - 1:
        size /= base
        idx += 1
    return f"{size:.{precision}f} {units[idx]}"


@dataclass(slots=True)
class LogseqPath:
    """LogseqPath class."""

    file: Path
    context: LogseqFileContext
    file_type: str = ""
    logseq_url: str = ""
    name: str = ""
    uri: str = field(init=False)
    _stat: stat_result = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqPath object."""
        self._stat = self.file.stat()
        self.uri: str = self.file.as_uri()
        _filenamer = LogseqFileName(
            journal_format=self.context.journal_format,
            ns_file_sep=self.context.ns_file_sep,
            journal_dir=self.context.journal_dir,
        )
        self.name = _filenamer(self.file)
        self.file_type = self.evaluate_file_type()
        self.logseq_url = self.set_logseq_url()

    def evaluate_file_type(self) -> str:
        """Determine the file type based on the directory structure."""
        _result = self.context.result_map.get(self.file.parent.name, (FileType.OTHER, FileType.OTHER))
        if _result[0] != FileType.OTHER:
            return _result[0]
        for key, _result in self.context.result_map.items():
            if key in self.file.parts:
                return _result[1]
        return FileType.OTHER

    def set_logseq_url(self) -> str:
        """Set the Logseq URL."""
        uri_path = Path(self.uri)
        target_index = len(uri_path.parts) - len(self.context.graph_path.parts)
        target_segment = uri_path.parts[target_index]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            logger.warning("Invalid target segment for Logseq URL: %s", target_segments_to_final)
            return ""
        graph_path = str(self.context.graph_path).replace("\\", "/")
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

    @property
    def timestamp_info(self) -> TimestampInfo:
        """Get the timestamps for the file."""
        return TimestampInfo(
            time_existed=self.context.now_ts - self._stat.st_birthtime,
            time_unmodified=self.context.now_ts - self._stat.st_mtime,
            date_created=datetime.fromtimestamp(self._stat.st_birthtime, tz=UTC).isoformat(),
            date_modified=datetime.fromtimestamp(self._stat.st_mtime, tz=UTC).isoformat(),
        )

    @property
    def size_info(self) -> SizeInfo:
        """Get the size information for the file."""
        return SizeInfo(
            size=self._stat.st_size,
            human_readable_size=format_bytes(self._stat.st_size),
            has_content=bool(self._stat.st_size),
        )

    @property
    def namespace_info(self) -> NamespaceInfo:
        """Get the namespace name data."""
        _ns_parts = self.name.split(Core.NS_SEP)
        return NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts, start=1)},
            root=_ns_parts[0],
            parent=_ns_parts[-2] if len(_ns_parts) > 2 else _ns_parts[0],
            parent_full=Core.NS_SEP.join(_ns_parts[:-1]),
            stem=_ns_parts[-1],
            is_namespace=Core.NS_SEP in self.name,
        )
