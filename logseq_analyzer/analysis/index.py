"""
FilIndex class.
"""

from collections import defaultdict
from typing import Dict, Generator, List, Set, Union
from pathlib import Path

from ..logseq_file.file import LogseqFile
from ..utils.helpers import singleton


@singleton
class FileIndex:
    """Class to index files in the Logseq graph."""

    def __init__(self):
        """Initialize the FileIndex instance."""
        self.files: Set[LogseqFile] = set()
        self.hash_to_file: Dict[int, LogseqFile] = {}
        self.name_to_files: Dict[str, List[LogseqFile]] = defaultdict(list)
        self.path_to_file: Dict[Path, LogseqFile] = {}

    def __repr__(self):
        """Return a string representation of the FileIndex."""
        return "FileIndex()"

    def __str__(self):
        """Return a string representation of the FileIndex."""
        return "FileIndex"

    def __len__(self):
        """Return the number of files in the index."""
        return len(self.files)

    def add(self, file: LogseqFile):
        """Add a file to the index."""
        self.files.add(file)
        self.hash_to_file[file] = file
        self.name_to_files[file.path.name].append(file)
        self.path_to_file[file.file_path] = file

    def get(self, key) -> Union[LogseqFile, List[LogseqFile], None]:
        """Get a file by its key."""
        if isinstance(key, int):
            return self.hash_to_file.get(key)
        if isinstance(key, str):
            return self.name_to_files.get(key, [])
        if isinstance(key, Path):
            return self.path_to_file.get(key)
        raise TypeError(f"Invalid key type: {type(key)}. Expected int, str, or Path.")

    def remove(self, key):
        """Remove a file from the index."""
        if isinstance(key, LogseqFile):
            if key in self.files:
                self.files.remove(key)
                del self.hash_to_file[key]
                self.name_to_files[key.path.name].remove(key)
                if not self.name_to_files[key.path.name]:
                    del self.name_to_files[key.path.name]
                del self.path_to_file[key.file_path]
            print(f"Key {key} removed from index.")
        elif isinstance(key, int):
            file = self.hash_to_file.pop(key, None)
            if file:
                self.files.remove(file)
                self.name_to_files[file.path.name].remove(file)
                if not self.name_to_files[file.path.name]:
                    del self.name_to_files[file.path.name]
                del self.path_to_file[file.file_path]
            print(f"Key {key} removed from index.")
        elif isinstance(key, str):
            files = self.name_to_files.pop(key, [])
            for file in files:
                self.files.remove(file)
                del self.hash_to_file[file]
                del self.path_to_file[file.file_path]
            print(f"Key {key} removed from index.")
        elif isinstance(key, Path):
            file = self.path_to_file.pop(key, None)
            if file:
                self.files.remove(file)
                del self.hash_to_file[file]
                self.name_to_files[file.path.name].remove(file)
                if not self.name_to_files[file.path.name]:
                    del self.name_to_files[file.path.name]
            print(f"Key {key} removed from index.")

    def list_files_with_keys_and_values(self, **criteria) -> List[LogseqFile]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for file in self.files:
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file)
        return result

    def list_file_names_with_keys_and_values(self, **criteria) -> List[str]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for file in self.files:
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.path.name)
        return result

    def list_file_names_without_keys(self, *criteria) -> List[str]:
        """Extract a subset of the summary data based on whether the keys do not exist."""
        result = []
        for file in self.files:
            if all(not hasattr(file, key) for key in criteria):
                result.append(file.path.name)
        return result

    def yield_files_with_keys(self, *criteria) -> Generator[LogseqFile, None, None]:
        """Extract a subset of the summary data based on whether the keys exists."""
        for file in self.files:
            if all(hasattr(file, key) for key in criteria):
                yield file
