"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

import logging
from datetime import datetime
from pathlib import Path


class LogseqFilestats:
    """LogseqFilestats class."""

    def __init__(self, file_path: Path) -> None:
        """Post-initialization method to set file statistics attributes."""

        self.file_path = file_path
        stat = file_path.stat()
        size = stat.st_size
        self.size = size
        self.has_content = bool(size)

        try:
            _created_ts = stat.st_birthtime
        except AttributeError:
            _created_ts = stat.st_ctime
            logging.warning(
                "st_birthtime not available for %s. Using st_ctime instead.",
                file_path,
            )
        _modified_ts = stat.st_mtime
        _now = datetime.now()
        self.time_existed = _now.timestamp() - _created_ts
        self.time_unmodified = _now.timestamp() - _modified_ts
        self.date_created = datetime.fromtimestamp(_created_ts).isoformat()
        self.date_modified = datetime.fromtimestamp(_modified_ts).isoformat()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}({self.file_path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqFilestats object."""
        return f"{self.__class__.__qualname__}: {self.file_path}"
