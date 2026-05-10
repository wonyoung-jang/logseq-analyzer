"""Module for handling caching mechanisms for the application."""

import logging
import shelve
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.domain.index import FileIndex
from logseq_analyzer.utils.enums import Format

if TYPE_CHECKING:
    from collections.abc import Iterator


logger = logging.getLogger(__name__)


class CacheKey(StrEnum):
    """Cache keys for the Logseq Analyzer."""

    INDEX = "index"
    MOD_TRACKER = "mod_tracker"


@dataclass(slots=True)
class Cache:
    """Cache class to manage caching of modified files and directories."""

    path: Path
    graph_dir: Path
    graph_cache: bool
    target_dirs: set[str]
    cache: shelve.Shelf = field(init=False)

    def open(self, protocol: int = 5) -> None:
        """Open the cache file."""
        self.cache = shelve.open(self.path, protocol=protocol)  # noqa: SIM115

    def close(self, index: FileIndex) -> None:
        """Close the cache file."""
        self.cache[CacheKey.INDEX] = index
        self.cache.close()

    def iter_modified_files(self) -> Iterator[Path]:
        """Get the modified files from the cache."""
        mod_tracker = {}
        if CacheKey.MOD_TRACKER in self.cache:
            mod_tracker = self.cache[CacheKey.MOD_TRACKER]
        for path in self._iter_files():
            _str_path = str(path)
            _curr_mtime = path.stat().st_mtime
            if _curr_mtime == mod_tracker.get(_str_path):
                continue
            mod_tracker[_str_path] = _curr_mtime
            yield path
        self.cache[CacheKey.MOD_TRACKER] = mod_tracker

    def initialize(self) -> FileIndex:
        """Clear the cache if needed."""
        if self.graph_cache:
            self.cache.close()
            self.path.unlink(missing_ok=True)
            self.open()
            logger.info("Cache cleared and reset index.")
            return FileIndex()
        index = self.cache[CacheKey.INDEX] if CacheKey.INDEX in self.cache else FileIndex()
        index.remove_deleted_files()
        self.cache[CacheKey.INDEX] = index
        logger.info("Cache not cleared, checking for deleted files.")
        return index

    def _iter_files(self) -> Iterator[Path]:
        """Recursively iterate over files in the root directory."""
        for root, dirs, files in Path.walk(self.graph_dir):
            if root == self.graph_dir:
                continue
            if any(name in self.target_dirs for name in (root.name, root.parent.name)):
                for file in files:
                    if Path(file).suffix == Format.ORG:
                        logger.info("Skipping org-mode file %s in %s", file, root)
                        continue
                    yield root / file
            else:
                logger.info("Skipping directory %s outside target directories", root)
                dirs.clear()
