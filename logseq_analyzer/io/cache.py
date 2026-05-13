"""Module for handling caching mechanisms for the application."""

import logging
import shelve
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from logseq_analyzer.domain.model import FileIndex

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path


logger = logging.getLogger(__name__)


class CacheKey(StrEnum):
    """Cache keys for the Logseq Analyzer."""

    INDEX = "index"
    MODTIMES = "mod_tracker"


@dataclass(slots=True)
class Cache:
    """Cache class to manage caching of modified files and directories."""

    path: Path

    def save(self, index: FileIndex) -> None:
        """Close the cache file."""
        with shelve.open(self.path) as db:
            db[CacheKey.INDEX] = index

    def reset(self) -> FileIndex:
        """Reset the cache by clearing it and returning a new FileIndex."""
        with shelve.open(self.path) as db:
            index = FileIndex()
            db[CacheKey.INDEX] = index
            db[CacheKey.MODTIMES] = {}
            return index

    def load(self) -> FileIndex:
        """Load the index from the cache, removing any deleted files from the index."""
        with shelve.open(self.path) as db:
            index: FileIndex = db.get(CacheKey.INDEX, FileIndex())
            index.remove_deleted_files()
            db[CacheKey.INDEX] = index
            return index

    def get_modified(self, files: Iterator[Path]) -> Iterable[Path]:
        """Get the modified files from the cache."""
        with shelve.open(self.path) as db:
            modtimes = db.get(CacheKey.MODTIMES, {})
            modified = []
            for path in files:
                _path = str(path)
                _curr_mtime = path.stat().st_mtime
                if _curr_mtime != modtimes.get(_path):
                    modtimes[_path] = _curr_mtime
                    modified.append(path)
            db[CacheKey.MODTIMES] = modtimes
        return modified
