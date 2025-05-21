"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

import logging
from datetime import datetime
from os import stat_result
from pathlib import Path


class LogseqFilestats:
    """LogseqFilestats class."""

    __slots__ = (
        "file_path",
        "size",
        "has_content",
        "time_existed",
        "time_unmodified",
        "date_created",
        "date_modified",
    )

    _now_ts = datetime.now().timestamp()

    def __init__(self, file_path: Path) -> None:
        """Initialize the LogseqFilestats object."""
        self.file_path = file_path
        self.size: int = 0
        self.has_content: bool = False
        self.time_existed: float = 0.0
        self.time_unmodified: float = 0.0
        self.date_created: str = ""
        self.date_modified: str = ""

    def __repr__(self) -> str:
        """Return a string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}({self.file_path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}: {self.file_path}"

    def process_stats(self) -> None:
        """Process the file statistics."""
        _stat = self.file_path.stat()
        _size = _stat.st_size
        self.set_size_and_content(_size)
        self.set_timestamps(_stat)

    def set_size_and_content(self, _size: int) -> None:
        """Set the size and content attributes."""
        self.size = _size
        self.has_content = bool(_size)

    def set_timestamps(self, _stat: stat_result) -> None:
        """Set the timestamps attributes."""
        _now_ts = LogseqFilestats._now_ts
        _created_ts = self.get_created_timestamp(_stat)
        _modified_ts = _stat.st_mtime
        self.time_existed = _now_ts - _created_ts
        self.time_unmodified = _now_ts - _modified_ts
        self.set_string_timestamps(_created_ts, _modified_ts)

    def set_string_timestamps(self, _created_ts: float, _modified_ts: float) -> None:
        """Set the string representation of the timestamps."""
        self.date_created = datetime.fromtimestamp(_created_ts).isoformat()
        self.date_modified = datetime.fromtimestamp(_modified_ts).isoformat()

    def get_created_timestamp(self, _stat: stat_result) -> float:
        """Get the created timestamp of the file."""
        path = self.file_path
        try:
            return _stat.st_birthtime
        except AttributeError:
            logging.warning("st_birthtime not available for %s. Using st_ctime.", path)
            return _stat.st_ctime
