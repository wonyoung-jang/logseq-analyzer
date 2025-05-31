"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from os import stat_result
from pathlib import Path

from ..utils.helpers import format_bytes

logger = logging.getLogger(__name__)


@dataclass
class TimestampInfo:
    """File timestamp information class."""

    time_existed: float = 0.0
    time_unmodified: float = 0.0
    date_created: str = ""
    date_modified: str = ""


class LogseqFilestats:
    """LogseqFilestats class."""

    __slots__ = (
        "path",
        "size",
        "size_human_readable",
        "has_content",
        "ts_info",
    )

    _now_ts = datetime.now().timestamp()

    def __init__(self, path: Path) -> None:
        """Initialize the LogseqFilestats object."""
        self.path: Path = path
        self.size: int = 0
        self.size_human_readable: str = ""
        self.has_content: bool = False
        self.ts_info: TimestampInfo = TimestampInfo()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}({self.path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}: {self.path}"

    def process_stats(self) -> None:
        """Process the file statistics."""
        _stat = self.path.stat()
        self.set_size_and_content(_stat)
        self.set_timestamps(_stat)

    def set_size_and_content(self, stat: stat_result) -> None:
        """Set the size and content attributes."""
        _size = stat.st_size
        self.size = _size
        self.size_human_readable = format_bytes(_size)
        self.has_content = bool(_size)

    def set_timestamps(self, stat: stat_result) -> None:
        """Set the timestamps attributes."""
        _created_ts = self.get_created_timestamp(stat)
        _modified_ts = stat.st_mtime
        self.ts_info.time_existed = self._now_ts - _created_ts
        self.ts_info.time_unmodified = self._now_ts - _modified_ts
        self.ts_info.date_created = datetime.fromtimestamp(_created_ts).isoformat()
        self.ts_info.date_modified = datetime.fromtimestamp(_modified_ts).isoformat()

    def get_created_timestamp(self, stat: stat_result) -> float:
        """Get the created timestamp of the file."""
        try:
            return stat.st_birthtime
        except AttributeError:
            logger.warning("st_birthtime not available for %s. Using st_ctime.", self.path)
            return stat.st_ctime
