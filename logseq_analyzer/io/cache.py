"""
This module handles caching mechanisms for the application.
"""

import logging
import shelve
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

from ..utils.enums import CacheKeys
from ..utils.helpers import iter_files, singleton

if TYPE_CHECKING:
    from ..analysis.index import FileIndex

logger = logging.getLogger(__name__)


@singleton
class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    __slots__ = ("cache_path", "cache")

    def __init__(self, cache_path: Path = None) -> None:
        """Initialize the class."""
        self.cache_path: Path = cache_path
        self.cache: shelve.Shelf[Any] = None

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}(cache_path="{self.cache_path}")'

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.cache_path}"

    def open(self, protocol: int = 5) -> None:
        """Open the cache file."""
        self.cache = shelve.open(self.cache_path, protocol=protocol)

    def close(self) -> None:
        """Close the cache file."""
        self.cache.close()

    def update(self, data: Any) -> None:
        """Update the cache with new data."""
        self.cache.update(data)

    def get(self, key, default=None) -> Any | None:
        """Get a value from the cache."""
        return self.cache.get(key, default)

    def initialize(self, clear: bool, index: "FileIndex") -> None:
        """Clear the cache if needed."""
        if clear:
            self.clear()
            logger.info("Cache cleared.")
        else:
            self.clear_deleted_files(index)
            logger.info("Cache not cleared.")

    def clear(self) -> None:
        """Clear the cache."""
        self.close()
        self.cache_path.unlink(missing_ok=True)
        self.open()

    def clear_deleted_files(self, index: "FileIndex", index_key: str = CacheKeys.INDEX.value) -> None:
        """Clear the deleted files from the cache."""
        if index_key in self.cache:
            del index
            index = self.cache[index_key]
        index.remove_deleted_files()

    def iter_modified_files(
        self, graph_dir: Path, target_dirs: set[str], mod_tracker_key: str = CacheKeys.MOD_TRACKER.value
    ) -> Generator[Path, Any, None]:
        """Get the modified files from the cache."""
        mod_tracker = self.cache.setdefault(mod_tracker_key, {})
        for path in iter_files(graph_dir, target_dirs):
            str_path = str(path)
            curr_date_mod = path.stat().st_mtime
            if curr_date_mod == mod_tracker.get(str_path):
                continue
            mod_tracker[str_path] = curr_date_mod
            logger.debug("File modified: %s", path)
            yield path
        self.cache[mod_tracker_key] = mod_tracker
