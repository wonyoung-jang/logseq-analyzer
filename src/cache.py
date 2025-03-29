"""This module handles caching mechanisms for the application."""

from pathlib import Path
import logging
import shelve

from src.config_loader import Config
from src.logseq_graph import LogseqGraph

from .helpers import iter_files


class Cache:
    """
    Cache class to manage caching of modified files and directories.
    """

    instance = None

    def __init__(self, cache_path: str):
        """
        Initialize the Cache class with a given cache file path.
        """
        self.cache_path = Path(cache_path)
        self.cache = shelve.open(self.cache_path, protocol=5)

    @staticmethod
    def get_instance(cache_path: str = None):
        """
        Get the singleton instance of the Cache class.
        """
        if Cache.instance is None and cache_path:
            Cache.instance = Cache(cache_path)
        return Cache.instance

    def close(self):
        """
        Close the cache file.
        """
        self.cache.close()

    def update(self, data):
        """
        Update the cache with new data.
        """
        self.cache.update(data)

    def get(self, key, default=None):
        """
        Get a value from the cache.
        """
        return self.cache.get(key, default)

    def clear(self):
        """
        Clear the cache.
        """
        self.cache.clear()

    def iter_modified_files(self):
        """
        Get the modified files from the cache.
        """
        mod_tracker = self.cache.get("mod_tracker", {})
        config = Config.get_instance()
        graph = LogseqGraph.get_instance()
        target_dirs = config.get_logseq_target_dirs()

        for path in iter_files(graph.directory, target_dirs):
            curr_date_mod = path.stat().st_mtime
            last_date_mod = mod_tracker.get(str(path))

            if last_date_mod is None or last_date_mod != curr_date_mod:
                mod_tracker[str(path)] = curr_date_mod
                logging.debug("File modified: %s", path)
                yield path

        self.cache["mod_tracker"] = mod_tracker

    def clear_deleted_files(self) -> None:
        """
        Get the deleted files from the cache.
        """
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
