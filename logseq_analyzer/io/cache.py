"""
This module handles caching mechanisms for the application.
"""

import logging
import shelve
from pathlib import Path
from typing import Any, Generator

from ..analysis.index import FileIndex
from ..logseq_file.file import LogseqFile
from ..utils.enums import Output
from ..utils.helpers import iter_files, singleton


@singleton
class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    __slots__ = ("cache_path", "cache")

    def __init__(self, cache_path: Path) -> None:
        """Initialize the class."""
        self.cache_path = cache_path
        self.cache = shelve.open(cache_path, protocol=5)

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}(cache_path="{self.cache_path}")'

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.cache_path}"

    def close(self) -> None:
        """Close the cache file."""
        self.cache.close()

    def update(self, data: Any) -> None:
        """Update the cache with new data."""
        self.cache.update(data)

    def get(self, key, default=None) -> Any | None:
        """Get a value from the cache."""
        return self.cache.get(key, default)

    def clear(self) -> None:
        """Clear the cache."""
        self.close()
        self.cache_path.unlink()
        self.cache = shelve.open(self.cache_path, protocol=5)

    def clear_deleted_files(self, index: FileIndex) -> None:
        """Clear the deleted files from the cache."""
        if "index" in self.cache:
            del index
            index = self.cache["index"]
        files_to_remove = set(Cache._yield_deleted_files(index))
        for file in files_to_remove:
            logging.warning("File removed from index: %s", file.file_path)
            index.remove(file)

    def iter_modified_files(self, graph_dir: Path, target_dirs: set[str]) -> Generator[Path, Any, None]:
        """Get the modified files from the cache."""
        mod_tracker = self.cache.setdefault(Output.MOD_TRACKER.value, {})
        for path in iter_files(graph_dir, target_dirs):
            str_path = str(path)
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str_path)
            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str_path] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path
        self.cache[Output.MOD_TRACKER.value] = mod_tracker

    @staticmethod
    def _yield_deleted_files(index: FileIndex) -> Generator[LogseqFile, Any, None]:
        """Yield deleted files from the cache."""
        for file in index:
            if not file.file_path.exists():
                logging.debug("File deleted: %s", file)
                yield file
