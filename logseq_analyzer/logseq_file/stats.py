"""
This module defines the LogseqFilestats class, which is used to gather file statistics for Logseq files.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class LogseqFilestats:
    """
    LogseqFilestats class.
    """

    file_path: Path
    size: int = field(init=False, repr=False)
    has_content: bool = field(init=False, repr=False)
    time_existed: float = field(init=False, repr=False)
    time_unmodified: float = field(init=False, repr=False)
    date_created: str = field(init=False, repr=False)
    date_modified: str = field(init=False, repr=False)

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
