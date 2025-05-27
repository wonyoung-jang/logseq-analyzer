"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from os import stat_result
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileTimestampInfo:
    """File timestamp information class."""

    time_existed: float = 0.0
    time_unmodified: float = 0.0
    date_created: str = ""
    date_modified: str = ""


class LogseqFilestats:
    """LogseqFilestats class."""

    __slots__ = (
        "file_path",
        "size",
        "has_content",
        "timestamps",
    )

    _now_ts = datetime.now().timestamp()

    def __init__(self, file_path: Path) -> None:
        """Initialize the LogseqFilestats object."""
        self.file_path: Path = file_path
        self.size: int = 0
        self.has_content: bool = False
        self.timestamps: FileTimestampInfo = FileTimestampInfo()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}({self.file_path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}: {self.file_path}"

    def process_stats(self) -> None:
        """Process the file statistics."""
        _stat = self.file_path.stat()
        self.set_size_and_content(_stat)
        self.set_timestamps(_stat)

    def set_size_and_content(self, stat: stat_result) -> None:
        """Set the size and content attributes."""
        _size = stat.st_size
        self.size = _size
        self.has_content = bool(_size)

    def set_timestamps(self, stat: stat_result) -> None:
        """Set the timestamps attributes."""
        _now_ts = LogseqFilestats._now_ts
        _created_ts = self.get_created_timestamp(stat)
        _modified_ts = stat.st_mtime
        self.timestamps.time_existed = _now_ts - _created_ts
        self.timestamps.time_unmodified = _now_ts - _modified_ts
        self.timestamps.date_created = datetime.fromtimestamp(_created_ts).isoformat()
        self.timestamps.date_modified = datetime.fromtimestamp(_modified_ts).isoformat()

    def get_created_timestamp(self, stat: stat_result) -> float:
        """Get the created timestamp of the file."""
        try:
            return stat.st_birthtime
        except AttributeError:
            logger.warning("st_birthtime not available for %s. Using st_ctime.", self.file_path)
            return stat.st_ctime
