"""
This module handles caching mechanisms for the application.

Imported once in app.py
"""

import logging
import shelve
from pathlib import Path
from typing import Any, Generator

from ..analysis.index import FileIndex
from ..config.analyzer_config import LogseqAnalyzerConfig
from ..logseq_file.file import LogseqFile
from ..utils.enums import Output, OutputDir
from ..utils.helpers import iter_files, singleton
from .filesystem import CacheFile, GraphDirectory


@singleton
class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    __slots__ = ("cache_path", "cache")

    def __init__(self, cache_file: CacheFile = None) -> None:
        """Initialize the class."""
        if cache_file is None:
            cache_file = CacheFile()
        self.cache_path = cache_file.path
        self.cache = shelve.open(self.cache_path, protocol=5)

    def __repr__(self) -> str:
        return f'Cache(cache_path="{self.cache_path}")'

    def __str__(self) -> str:
        return f"Cache: {self.cache_path}"

    def close(self) -> None:
        """Close the cache file."""
        self.cache.close()

    def update(self, data: dict) -> None:
        """Update the cache with new data."""
        self.cache.update(data)

    def get(self, key, default=None) -> Any | None:
        """Get a value from the cache."""
        return self.cache.get(key, default)

    def clear(self) -> None:
        """Clear the cache."""
        self.cache.close()
        self.cache_path.unlink()
        self.cache = shelve.open(self.cache_path, protocol=5)

    def clear_deleted_files(self) -> None:
        """Clear the deleted files from the cache."""
        analysis_keys = [
            OutputDir.JOURNALS.value,
            OutputDir.SUMMARY_FILES.value,
            OutputDir.SUMMARY_CONTENT.value,
            OutputDir.NAMESPACES.value,
            OutputDir.MOVED_FILES.value,
        ]
        for key in analysis_keys:
            if key in self.cache:
                self.cache[key] = {}

        index_keys = [
            Output.FILES.value,
            Output.HASH_TO_FILE.value,
            Output.NAME_TO_FILES.value,
            Output.PATH_TO_FILE.value,
        ]
        index: FileIndex = FileIndex()
        if OutputDir.META.value in self.cache:
            for key in index_keys:
                if key in self.cache[OutputDir.META.value]:
                    setattr(index, key, self.cache[OutputDir.META.value][key])

        files_to_remove = set()
        for file in self.yield_deleted_files(index):
            files_to_remove.add(file)
            logging.debug("File removed from index: %s", file.file_path)
        for file in files_to_remove:
            index.remove(file)

    def yield_deleted_files(self, index: FileIndex) -> Generator[LogseqFile, Any, None]:
        """Yield deleted files from the cache."""
        for file in index.files:
            if not file.file_path.exists():
                logging.debug("File deleted: %s", file.file_path)
                yield file

    def iter_modified_files(self) -> Generator[Path, Any, None]:
        """Get the modified files from the cache."""
        mod_tracker = self.cache.setdefault(Output.MOD_TRACKER.value, {})
        gd = GraphDirectory()
        graph_dir = gd.path
        lac = LogseqAnalyzerConfig()
        target_dirs = lac.target_dirs
        for path in iter_files(graph_dir, target_dirs):
            str_path = str(path)
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str_path)
            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str_path] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path
        self.cache[Output.MOD_TRACKER.value] = mod_tracker
