"""
This module handles caching mechanisms for the application.

Imported once in app.py
"""

from pathlib import Path
import logging
import shelve

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import iter_files
from .path_validator import LogseqAnalyzerPathValidator


class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    _instance = None

    def __new__(cls, *args):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cache_path: Path = "logseq-analyzer-cache"):
        """Initialize the class."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._paths = LogseqAnalyzerPathValidator()
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

    def iter_modified_files(self):
        """Get the modified files from the cache."""
        mod_tracker = self.cache.get("mod_tracker", {})
        graph = self._paths.dir_graph.path
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
