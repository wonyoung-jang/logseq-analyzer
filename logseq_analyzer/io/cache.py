"""
This module handles caching mechanisms for the application.

Imported once in app.py
"""

import logging
import shelve

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.enums import Output
from ..utils.helpers import iter_files, singleton
from .filesystem import CacheFile, GraphDirectory


@singleton
class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    def __init__(self):
        """Initialize the class."""
        self.cache = shelve.open(CacheFile().path, protocol=5)

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
        meta_data = self.cache.setdefault("META_REPORTS", {})
        meta_data.setdefault(Output.HASH_TO_FILE.value, {})
        for hash_ in self.yield_deleted_files():
            meta_data[Output.HASH_TO_FILE.value].pop(hash_, None)
        self.cache["META_REPORTS"][Output.HASH_TO_FILE.value] = meta_data[Output.HASH_TO_FILE.value]

    def yield_deleted_files(self):
        """Yield deleted files from the cache."""
        meta_data = self.cache.setdefault("META_REPORTS", {})
        for hash_, file in meta_data[Output.HASH_TO_FILE.value].items():
            if file.file_path.exists():
                continue

            logging.debug("File deleted: %s", file.file_path)
            yield hash_

    def iter_modified_files(self):
        """Get the modified files from the cache."""
        mod_tracker = self.cache.get("mod_tracker", {})
        graph_dir = GraphDirectory().path
        target_dirs = LogseqAnalyzerConfig().target_dirs
        for path in iter_files(graph_dir, target_dirs):
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str(path))
            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str(path)] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path
        self.cache["mod_tracker"] = mod_tracker


@singleton
class ModTracker:
    """
    Modification tracker class to track modifications in files.
    """

    def __init__(self):
        """Initialize the class."""
        self.data = {}
