"""
This module handles caching mechanisms for the application.

Imported once in app.py
"""

from pathlib import Path
import logging
import shelve

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import iter_files, singleton
from .path_validator import LogseqAnalyzerPathValidator


@singleton
class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    def __init__(self):
        """Initialize the class."""
        LogseqAnalyzerPathValidator().validate_cache()
        self.cache = shelve.open(LogseqAnalyzerPathValidator().file_cache.path, protocol=5)

    def close(self):
        """Close the cache file."""
        self.cache.close()

    def update(self, data):
        """Update the cache with new data."""
        self.cache.update(data)

    def get(self, key, default=None):
        """Get a value from the cache."""
        return self.cache.get(key, default)

    def iter_modified_files(self):
        """Get the modified files from the cache."""
        mod_tracker = self.cache.get("mod_tracker", {})
        graph = LogseqAnalyzerPathValidator().dir_graph.path
        targets = LogseqAnalyzerConfig().target_dirs
        for path in iter_files(graph, targets):
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str(path))
            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str(path)] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path
        self.cache["mod_tracker"] = mod_tracker

    def clear(self):
        """Clear the cache."""
        self.cache.clear()

    def clear_deleted_files(self):
        """Clear the deleted files from the cache."""
        self.cache.setdefault("___meta___graph_data", {})
        self.cache.setdefault("___meta___graph_content", {})
        for file in self.yield_deleted_files():
            self.cache["___meta___graph_data"].pop(file, None)
            self.cache["___meta___graph_content"].pop(file, None)

    def yield_deleted_files(self):
        """Yield deleted files from the cache."""
        for key, data in self.cache["___meta___graph_data"].items():
            path = data.get("file_path")
            if Path(path).exists():
                continue
            logging.debug("File deleted: %s", path)
            yield key
