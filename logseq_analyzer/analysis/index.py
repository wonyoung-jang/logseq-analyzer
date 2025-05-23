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

    __slots__ = ("files", "hash_to_file", "name_to_files", "path_to_file")

    def __init__(self) -> None:
        """
        Initialize the FileIndex instance.
        """
        self.files: set[LogseqFile] = set()
        self.hash_to_file: dict[int, LogseqFile] = {}
        self.name_to_files: dict[str, list[LogseqFile]] = defaultdict(list)
        self.path_to_file: dict[Path, LogseqFile] = {}

    def __repr__(self) -> str:
        """Return a string representation of the FileIndex."""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """Return a string representation of the FileIndex."""
        return f"{self.__class__.__name__}"

    def __len__(self) -> int:
        """Return the number of files in the index."""
        return len(self.files)

    def __iter__(self) -> Iterator[LogseqFile]:
        """Iterate over the files in the index."""
        return iter(self.files)

    def __getitem__(self, key) -> Any:
        """Get a file by its key."""
        if isinstance(key, LogseqFile):
            if key in self:
                return key
            raise KeyError(f"File {key} not found in index.")
        if isinstance(key, int):
            return self.hash_to_file.get(key)
        if isinstance(key, str):
            return self.name_to_files.get(key, [])
        if isinstance(key, Path):
            return self.path_to_file.get(key)
        raise TypeError(f"Invalid key type: {type(key)}. Expected int, str, or Path.")

    def __contains__(self, key) -> bool:
        """Check if a file is in the index."""
        if isinstance(key, LogseqFile):
            return key in self.files
        if isinstance(key, int):
            return key in self.hash_to_file
        if isinstance(key, str):
            return key in self.name_to_files
        if isinstance(key, Path):
            return key in self.path_to_file
        raise TypeError(f"Invalid key type: {type(key)}. Expected LogseqFile, int, str, or Path.")

    def add(self, file: LogseqFile) -> None:
        """Add a file to the index."""
        self.files.add(file)
        self.hash_to_file[hash(file)] = file
        self.name_to_files[file.path.name].append(file)
        self.path_to_file[file.file_path] = file

    def remove(self, key: Any) -> None:
        """Remove a file from the index."""
        files = self.files
        hash_to_file = self.hash_to_file
        name_to_files = self.name_to_files
        path_to_file = self.path_to_file
        if isinstance(key, LogseqFile):
            if key in self:
                file = key
                name = file.path.name
                files.remove(file)
                del hash_to_file[hash(file)]
                name_to_files[name].remove(file)
                if not name_to_files[name]:
                    del name_to_files[name]
                del path_to_file[file.file_path]
            logging.debug("Key %s removed from index.", key)
        elif isinstance(key, int):
            if file := hash_to_file.pop(key, None):
                name = file.path.name
                files.remove(file)
                name_to_files[name].remove(file)
                if not name_to_files[name]:
                    del name_to_files[name]
                del path_to_file[file.file_path]
            logging.debug("Key %s removed from index.", key)
        elif isinstance(key, str):
            for file in name_to_files.pop(key, []):
                files.remove(file)
                del hash_to_file[hash(file)]
                del path_to_file[file.file_path]
            logging.debug("Key %s removed from index.", key)
        elif isinstance(key, Path):
            if file := path_to_file.pop(key, None):
                name = file.path.name
                files.remove(file)
                del hash_to_file[hash(file)]
                name_to_files[name].remove(file)
                if not name_to_files[name]:
                    del name_to_files[name]
            logging.debug("Key %s removed from index.", key)

    def yield_files_with_keys_and_values(self, **criteria) -> Generator[LogseqFile, None, None]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        for file in self:
            for key, expected in criteria.items():
                if not hasattr(file, key):
                    break
                if not getattr(file, key) == expected:
                    break
            else:
                yield file
