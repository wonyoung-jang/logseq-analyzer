"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging


@dataclass
class LogseqFilestats:
    """Initialize the LogseqFilestats class."""

    file_path: Path
    size: int = 0
    has_content: bool = False
    time_existed: float = 0.0
    time_unmodified: float = 0.0
    date_created: datetime = None
    date_modified: datetime = None

    def __post_init__(self):
        """Post-initialization method to set file statistics attributes."""

        stat = self.file_path.stat()
        self.size = stat.st_size
        self.has_content = bool(self.size)

        now = datetime.now()
        try:
            created_ts = stat.st_birthtime
        except AttributeError:
            created_ts = stat.st_ctime
            logging.warning(
                "st_birthtime not available for %s. Using st_ctime instead.",
                self.file_path,
            )
        date_created = datetime.fromtimestamp(created_ts)
        date_modified = datetime.fromtimestamp(stat.st_mtime)
        self.time_existed = (now - date_created).total_seconds()
        self.time_unmodified = (now - date_modified).total_seconds()
        self.date_created = date_created.isoformat()
        self.date_modified = date_modified.isoformat()

    def __repr__(self):
        return f"LogseqFilestats({self.file_path})"
