"""
This module handles caching mechanisms for the application.

Imported once in app.py
"""

from pathlib import Path
import logging
import shelve

from .helpers import iter_files
from .logseq_analyzer_config import LogseqAnalyzerConfig
from .logseq_graph_config import LogseqGraphConfig

ANALYZER_CONFIG = LogseqAnalyzerConfig()
GRAPH_CONFIG = LogseqGraphConfig()


class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the class."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.cache = shelve.open(ANALYZER_CONFIG.config["CONST"]["CACHE"], protocol=5)

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

    def iter_modified_files(self):
        """Get the modified files from the cache."""
        mod_tracker = self.cache.get("mod_tracker", {})
        graph_dir = GRAPH_CONFIG.directory
        target_dirs = ANALYZER_CONFIG.target_dirs
        for path in iter_files(graph_dir, target_dirs):
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str(path))
            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str(path)] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path
        self.cache["mod_tracker"] = mod_tracker

    def clear_deleted_files(self):
        """Clear the deleted files from the cache."""
        deleted_files = []
        self.cache.setdefault("___meta___graph_data", {})
        self.cache.setdefault("___meta___graph_content", {})

        for key, data in self.cache["___meta___graph_data"].items():
            path = data.get("file_path")
            if Path(path).exists():
                continue
            deleted_files.append(key)
            logging.debug("File deleted: %s", path)

        for file in deleted_files:
            self.cache["___meta___graph_data"].pop(file, None)
            self.cache["___meta___graph_content"].pop(file, None)
