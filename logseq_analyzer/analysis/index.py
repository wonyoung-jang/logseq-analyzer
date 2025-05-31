"""
FileIndex class.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Generator, Iterator

from ..logseq_file.file import LogseqFile
from ..utils.enums import Output
from ..utils.helpers import singleton, yield_attrs

logger = logging.getLogger(__name__)


__all__ = [
    "FileIndex",
]


@singleton
class FileIndex:
    """Class to index files in the Logseq graph."""

    __slots__ = ("_files", "_hash_to_file", "_name_to_files", "_path_to_file")

    def __init__(self) -> None:
        """
        Initialize the FileIndex instance.
        """
        self._files: set[LogseqFile] = set()
        self._hash_to_file: dict[int, LogseqFile] = {}
        self._name_to_files: dict[str, list[LogseqFile]] = defaultdict(list)
        self._path_to_file: dict[Path, LogseqFile] = {}

    def __repr__(self) -> str:
        """Return a string representation of the FileIndex."""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """Return a string representation of the FileIndex."""
        return f"{self.__class__.__name__}"

    def __len__(self) -> int:
        """Return the number of files in the index."""
        return len(self._files)

    def __iter__(self) -> Iterator[LogseqFile]:
        """Iterate over the files in the index."""
        return iter(self._files)

    def __getitem__(self, key: Any) -> Any:
        """Get a file by its key."""
        if isinstance(key, LogseqFile):
            if key in self:
                return key
            raise KeyError(f"File {key} not found in index.")
        if isinstance(key, int):
            return self._hash_to_file.get(key)
        if isinstance(key, str):
            return self._name_to_files.get(key, [])
        if isinstance(key, Path):
            return self._path_to_file.get(key)
        raise TypeError(f"Invalid key type: {type(key).__name__}. Expected LogseqFile, int, str, or Path.")

    def __contains__(self, key: Any) -> bool:
        """Check if a file is in the index."""
        if isinstance(key, LogseqFile):
            return key in self._files
        if isinstance(key, int):
            return key in self._hash_to_file
        if isinstance(key, str):
            return key in self._name_to_files
        if isinstance(key, Path):
            return key in self._path_to_file
        raise TypeError(f"Invalid key type: {type(key).__name__}. Expected LogseqFile, int, str, or Path.")

    def add(self, file: LogseqFile) -> None:
        """Add a file to the index."""
        h = hash(file)
        name = file.path.name
        path = file.file_path
        self._files.add(file)
        self._hash_to_file[h] = file
        self._name_to_files[name].append(file)
        self._path_to_file[path] = file

    def remove(self, key: Any) -> None:
        """Strategy to remove a file from the index."""
        if isinstance(key, LogseqFile):
            target = key
        elif isinstance(key, int):
            target = self._hash_to_file.get(key)
        elif isinstance(key, str):
            for target in self._name_to_files.pop(key, []):
                self._remove_file(target)
            return
        elif isinstance(key, Path):
            target = self._path_to_file.get(key)
        else:
            raise TypeError(f"Invalid key type: {type(key).__name__}. Expected LogseqFile, int, str, or Path.")

        if target is None:
            logging.warning("Key %s not found in index.", key)
            return
        self._remove_file(target)
        logger.debug("Key %s removed from index.", key)

    def _remove_file(self, file: LogseqFile) -> None:
        """Helper method to remove a file from the index."""
        self._files.discard(file)
        self._hash_to_file.pop(hash(file), None)
        name = file.path.name
        if files := self._name_to_files.get(name):
            try:
                files.remove(file)
            except ValueError:
                logger.warning("File %s not found in name_to_files list for name %s.", file, name)
        else:
            del self._name_to_files[name]
        self._path_to_file.pop(file.file_path, None)

    def remove_deleted_files(self):
        """Remove deleted files from the cache."""
        for file in {f for f in self if not f.file_path.exists()}:
            self.remove(file)

    def filter_files(self, **criteria) -> Generator[LogseqFile, None, None]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        for file in self:
            for key, expected in criteria.items():
                if not hasattr(file, key):
                    break
                if not getattr(file, key) == expected:
                    break
            else:
                yield file

    def get_graph_data(self) -> dict[LogseqFile, dict[str, Any]]:
        """Get metadata file data from the graph."""
        graph_data = {}
        for file in self:
            data = {k: v for k, v in yield_attrs(file) if k not in ("content", "content_bullets", "primary_bullet")}
            graph_data[file] = data
        return graph_data

    def get_graph_content(self, write_graph: bool) -> dict[LogseqFile, Any]:
        """Get content data from the graph."""
        if not write_graph:
            return {}
        return {
            Output.GRAPH_BULLETS.value: {file: file.bullets.content_bullets for file in self},
            Output.GRAPH_CONTENT.value: {file: file.bullets.content for file in self},
        }

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the indexed files."""
        return {
            Output.GRAPH_DATA.value: self.get_graph_data(),
            Output.IDX_FILES.value: self._files,
            Output.IDX_HASH_TO_FILE.value: self._hash_to_file,
            Output.IDX_NAME_TO_FILES.value: self._name_to_files,
            Output.IDX_PATH_TO_FILE.value: self._path_to_file,
        }
