"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class LogseqFilestats:
    """
    LogseqFilestats class.
    """

    file_path: Path
    size: int = 0
    has_content: bool = False
    time_existed: float = 0.0
    time_unmodified: float = 0.0
    date_created: str = ""
    date_modified: str = ""

    def __post_init__(self) -> None:
        """Post-initialization method to set file statistics attributes."""

        stat = self.file_path.stat()
        self.size = stat.st_size
        self.has_content = bool(self.size)

        try:
            _created_ts = stat.st_birthtime
        except AttributeError:
            _created_ts = stat.st_ctime
            logging.warning(
                "st_birthtime not available for %s. Using st_ctime instead.",
                self.file_path,
            )
        _modified_ts = stat.st_mtime
        now = datetime.now()
        self.time_existed = now.timestamp() - _created_ts
        self.time_unmodified = now.timestamp() - _modified_ts
        self.date_created = datetime.fromtimestamp(_created_ts).isoformat()
        self.date_modified = datetime.fromtimestamp(_modified_ts).isoformat()
