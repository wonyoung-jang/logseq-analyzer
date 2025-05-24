"""
FileIndex class.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Generator, Iterator

from ..logseq_file.file import LogseqFile
from ..utils.helpers import singleton


def get_attribute_list(file_list: Generator[LogseqFile, None, None], attribute: str) -> list[Any]:
    """
    Get a list of attribute values from a list of LogseqFile objects.

    Args:
        file_list (Generator[LogseqFile, None, None]): generator of LogseqFile objects.
        attribute (str): The attribute to extract from each LogseqFile object.

    Returns:
        list[Union[str, int]]: list of attribute values.
    """
    return sorted(getattr(file, attribute) for file in file_list)


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

    def __getitem__(self, key: LogseqFile | int | str | Path) -> Any:
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

    def __contains__(self, key: LogseqFile | int | str | Path) -> bool:
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

    @property
    def files(self) -> set[LogseqFile]:
        """Return the set of files in the index."""
        return self._files

    @property
    def hash_to_file(self) -> dict[int, LogseqFile]:
        """Return the mapping of hashes to LogseqFile objects."""
        return self._hash_to_file

    @property
    def name_to_files(self) -> dict[str, list[LogseqFile]]:
        """Return the mapping of file names to lists of LogseqFile objects."""
        return self._name_to_files

    @property
    def path_to_file(self) -> dict[Path, LogseqFile]:
        """Return the mapping of file paths to LogseqFile objects."""
        return self._path_to_file

    def add(self, file: LogseqFile) -> None:
        """Add a file to the index."""
        h = hash(file)
        name = file.path.name
        path = file.file_path
        self._files.add(file)
        self._hash_to_file[h] = file
        self._name_to_files[name].append(file)
        self._path_to_file[path] = file

    def remove(self, key: LogseqFile | int | str | Path) -> None:
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
        logging.debug("Key %s removed from index.", key)

    def _remove_file(self, file: LogseqFile) -> None:
        """Helper method to remove a file from the index."""
        self._files.discard(file)
        self._hash_to_file.pop(hash(file), None)
        name = file.path.name
        if lst := self._name_to_files.get(name):
            try:
                lst.remove(file)
            except ValueError:
                logging.warning("File %s not found in name_to_files list for name %s.", file, name)
        else:
            del self._name_to_files[name]
        self._path_to_file.pop(file.file_path, None)

    def remove_deleted_files(self):
        """Remove deleted files from the cache.
        don't cause size errors"""
        to_delete = set()
        for file in self:
            if not file.file_path.exists():
                to_delete.add(file)
        for file in to_delete:
            self.remove(file)

    def yield_files_with_keys_and_values(self, **criteria) -> Generator[LogseqFile, None, None]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        for file in self:
            for key, expected in criteria.items():
                if not hasattr(file, key):
                    break
                if not getattr(file, key, None) == expected:
                    break
            else:
                yield file
