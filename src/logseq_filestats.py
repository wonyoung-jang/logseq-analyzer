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
        now = datetime.now().timestamp()

        self.file_count = stat.st_nlink
        self.size = stat.st_size
        self.date_modified = stat.st_mtime

        try:
            self.date_created = stat.st_birthtime
        except AttributeError:
            self.date_created = stat.st_ctime
            logging.warning("st_birthtime not available for %s. Using st_ctime instead.", self.file_path)

        self.time_existed = now - self.date_created
        self.time_unmodified = now - self.date_modified
