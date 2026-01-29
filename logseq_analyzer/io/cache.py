"""Module for handling caching mechanisms for the application."""

import logging
import shelve
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar

from ..analysis.index import FileIndex
from ..utils.helpers import iter_files

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from ..config.arguments import Args
    from ..io.filesystem import LogseqAnalyzerDirs

logger = logging.getLogger(__name__)


class CacheKey(StrEnum):
    """Cache keys for the Logseq Analyzer."""

    INDEX = "index"
    MOD_TRACKER = "mod_tracker"


@dataclass(slots=True)
class Cache:
    """Cache class to manage caching of modified files and directories."""

    cache_path: Path
    cache: shelve.Shelf[Any] = field(init=False)

    graph_dir: ClassVar[Path]
    graph_cache: ClassVar[bool] = False
    target_dirs: ClassVar[set[str]] = set()

    @classmethod
    def configure(cls, args: Args, analyzer_dirs: LogseqAnalyzerDirs) -> None:
        """Configure the Cache class with necessary settings.

        Args:
            args (Args): Command line arguments.
            analyzer_dirs (LogseqAnalyzerDirs): Directory paths for the Logseq analyzer.

        """
        cls.target_dirs = set(analyzer_dirs.target_dirs.values())
        cls.graph_dir = analyzer_dirs.graph_dirs.graph_dir.path
        cls.graph_cache = args.graph_cache

    def open(self, protocol: int = 5) -> None:
        """Open the cache file."""
        self.cache = shelve.open(self.cache_path, protocol=protocol)  # noqa: SIM115

    def close(self, index: FileIndex) -> None:
        """Close the cache file."""
        self.cache[CacheKey.INDEX] = index
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

    def clear_deleted_files(self) -> FileIndex:
        """Clear the deleted files from the cache."""
        index = self.cache[CacheKey.INDEX] if CacheKey.INDEX in self.cache else FileIndex()
        index.remove_deleted_files()
        self.cache[CacheKey.INDEX] = index
        return index

    def iter_modified_files(self) -> Generator[Path, Any]:
        """Get the modified files from the cache."""
        mod_tracker = {}
        if CacheKey.MOD_TRACKER in self.cache:
            mod_tracker = self.cache[CacheKey.MOD_TRACKER]

        file_iter = iter_files(Cache.graph_dir, Cache.target_dirs)
        for path in file_iter:
            str_path = str(path)
            curr_date_mod = path.stat().st_mtime
            if curr_date_mod == mod_tracker.get(str_path):
                continue
            mod_tracker[str_path] = curr_date_mod
            yield path

        self.cache[CacheKey.MOD_TRACKER] = mod_tracker
