"""This module handles caching mechanisms for the application."""

from pathlib import Path
import logging
import shelve

from .helpers import FileSystem
from .logseq_analyzer import ANALYZER
from .logseq_analyzer_config import ANALYZER_CONFIG
from .logseq_graph_config import GRAPH_CONFIG


class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    def __init__(self, analyzer, analyzer_config, graph_config):
        """Initialize the Cache class."""
        self.analyzer = analyzer
        self.analyzer_config = analyzer_config
        self.graph_config = graph_config
        self.cache = shelve.open(self.analyzer_config.get("CONST", "CACHE"), protocol=5)

    def close(self):
        """Close the cache file."""
        self.cache.close()

    def update(self, data):
        """Update the cache with new data."""
        self.cache.update(data)

    def get(self, key, default=None):
        """Get a value from the cache."""
        return self.cache.get(key, default)

    def choose_cache_clear(self):
        """Choose whether to clear the cache based on the graph_cache flag."""
        if self.analyzer.args.graph_cache:
            self.clear()
        else:
            self.clear_deleted_files()

    def clear(self):
        """Clear the cache."""
        self.cache.clear()

    def iter_modified_files(self):
        """Get the modified files from the cache."""
        mod_tracker = self.cache.get("mod_tracker", {})
        graph_dir = self.graph_config.directory
        target_dirs = self.analyzer_config.target_dirs
        for path in FileSystem(graph_dir, target_dirs).iter_files():
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


CACHE = Cache(ANALYZER, ANALYZER_CONFIG, GRAPH_CONFIG)
