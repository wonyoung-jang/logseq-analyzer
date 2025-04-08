"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path


@dataclass
class LogseqFilestats:
    """Initialize the LogseqFilestats class."""

    file_path: Path

    def __post_init__(self):
        """Post-initialization method to set file statistics attributes."""

        stat = self.file_path.stat()

        self.size = stat.st_size
        self.has_content = self.size > 0

        now = datetime.now()
        try:
            date_created = datetime.fromtimestamp(stat.st_birthtime)
        except AttributeError:
            date_created = datetime.fromtimestamp(stat.st_ctime)
            logging.warning(
                "st_birthtime not available for %s. Using st_ctime instead.",
                self.file_path,
            )
        date_modified = datetime.fromtimestamp(stat.st_mtime)
        self.time_existed = (now - date_created).total_seconds()
        self.time_unmodified = (now - date_modified).total_seconds()
        self.date_created = date_created.isoformat()
        self.date_modified = date_modified.isoformat()
