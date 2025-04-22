"""
This module handles caching mechanisms for the application.

Imported once in app.py
"""

import logging
import shelve

from ..analysis.index import FileIndex
from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.enums import Output, OutputDir
from ..utils.helpers import iter_files, singleton
from .filesystem import CacheFile, GraphDirectory


@singleton
class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    def __init__(self):
        """Initialize the class."""
        cache_file = CacheFile()
        cache_path = cache_file.path
        self.cache = shelve.open(cache_path, protocol=5)

    def close(self):
        """Close the cache file."""
        self.cache.close()

    def update(self, data):
        """Update the cache with new data."""
        self.cache.update(data)

    def get(self, key, default=None):
        """Get a value from the cache."""
        return self.cache.get(key, default)

    def clear(self):
        """Clear the cache."""
        self.cache.clear()

    def clear_deleted_files(self):
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
                del self.cache[key]

        if Output.FILE_INDEX.value in self.cache:
            index: FileIndex = self.cache[Output.FILE_INDEX.value]
        else:
            return

        files_to_remove = set()
        for file in self.yield_deleted_files(index):
            files_to_remove.add(file)
            logging.debug("File removed from index: %s", file.file_path)
        for file in files_to_remove:
            index.remove(file)

        self.cache[Output.FILE_INDEX.value] = index

    def yield_deleted_files(self, index: FileIndex):
        """Yield deleted files from the cache."""
        for file in index.files:
            if not file.file_path.exists():
                logging.debug("File deleted: %s", file.file_path)
                yield file

    def iter_modified_files(self):
        """Get the modified files from the cache."""
        mod_tracker = self.cache.setdefault(Output.MOD_TRACKER.value, {})
        graph_directory = GraphDirectory()
        graph_dir = graph_directory.path
        ls_analyzer_config = LogseqAnalyzerConfig()
        target_dirs = ls_analyzer_config.target_dirs
        for path in iter_files(graph_dir, target_dirs):
            str_path = str(path)
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str_path)
            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str_path] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path
        self.cache[Output.MOD_TRACKER.value] = mod_tracker
