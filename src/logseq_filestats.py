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

        now = datetime.now().timestamp()
        try:
            self.date_created = stat.st_birthtime
        except AttributeError:
            self.date_created = stat.st_ctime
            logging.warning("st_birthtime not available for %s. Using st_ctime instead.", self.file_path)
        self.date_modified = stat.st_mtime
        self.time_existed = now - self.date_created
        self.time_unmodified = now - self.date_modified
        self.read_date_created = datetime.fromtimestamp(self.date_created)
        self.read_date_modified = datetime.fromtimestamp(self.date_modified)
        self.read_time_existed = datetime.fromtimestamp(self.time_existed)
        self.read_time_unmodified = datetime.fromtimestamp(self.time_unmodified)
