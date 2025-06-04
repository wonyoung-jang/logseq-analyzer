"""
This module handles caching mechanisms for the application.
"""

import logging
import shelve
from pathlib import Path
from typing import Any, Generator

from ..analysis.index import FileIndex
from ..config.arguments import Args
from ..utils.enums import CacheKeys
from ..utils.helpers import iter_files
from ..io.filesystem import LogseqAnalyzerDirs

logger = logging.getLogger(__name__)


class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    __slots__ = ("cache_path", "cache")

    graph_dir: Path = None
    graph_cache: bool = False
    target_dirs: set[str] = set()

    def __init__(self, cache_path: Path = None) -> None:
        """Initialize the class."""
        self.cache_path: Path = cache_path
        self.cache: shelve.Shelf[Any] = None

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}(cache_path="{self.cache_path}")'

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.cache_path}"

    @classmethod
    def configure(cls, args: Args, analyzer_dirs: LogseqAnalyzerDirs) -> None:
        """
        Configure the Cache class with necessary settings.

        Args:
            args (Args): Command line arguments.
            analyzer_dirs (LogseqAnalyzerDirs): Directory paths for the Logseq analyzer.
        """
        cls.target_dirs = set(analyzer_dirs.target_dirs.values())
        cls.graph_dir = analyzer_dirs.graph_dirs.graph_dir.path
        cls.graph_cache = args.graph_cache

    def open(self, protocol: int = 5, writeback: bool = True) -> None:
        """Open the cache file."""
        self.cache = shelve.open(self.cache_path, protocol=protocol, writeback=writeback)

    def close(self, index: FileIndex, index_key: str = CacheKeys.INDEX.value) -> None:
        """Close the cache file."""
        self.cache[index_key] = index
        self.cache.sync()
        self.cache.close()

    def initialize(self) -> FileIndex:
        """Clear the cache if needed."""
        if Cache.graph_cache:
            self.clear()
            logger.info("Cache cleared and reset index.")
            return FileIndex()
        index = self.clear_deleted_files()
        logger.info("Cache not cleared, checking for deleted files.")
        return index

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.close()
        self.cache_path.unlink(missing_ok=True)
        self.open()

    def clear_deleted_files(self, index_key: str = CacheKeys.INDEX.value) -> FileIndex:
        """Clear the deleted files from the cache."""
        if index_key in self.cache:
            index = self.cache[index_key]
            del self.cache[index_key]
        else:
            index = FileIndex()
        index.remove_deleted_files()
        return index

    def iter_modified_files(self, mod_key: str = CacheKeys.MOD_TRACKER.value) -> Generator[Path, Any, None]:
        """Get the modified files from the cache."""
        mod_tracker = {}
        if mod_key in self.cache:
            mod_tracker = self.cache[mod_key]
            del self.cache[mod_key]

        file_iter = iter_files(Cache.graph_dir, Cache.target_dirs)
        for path in file_iter:
            str_path = str(path)
            curr_date_mod = path.stat().st_mtime
            if curr_date_mod == mod_tracker.get(str_path):
                continue
            mod_tracker[str_path] = curr_date_mod
            yield path

        self.cache[mod_key] = mod_tracker
