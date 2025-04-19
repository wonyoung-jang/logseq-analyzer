"""
FilIndex class.
"""

from collections import defaultdict
from typing import Dict, List, Set
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

    def __len__(self):
        """Return the number of files in the index."""
        return len(self.files)

    def __contains__(self, file):
        """Check if a file is in the index."""
        return file in self.files

    def add(self, file: LogseqFile):
        """Add a file to the index."""
        self.files.add(file)
        self.hash_to_file[file] = file
        self.name_to_files[file.path.name].append(file)
        self.path_to_file[file.file_path] = file

    def get(self, key):
        """Get a file by its key."""
        if isinstance(key, int):
            return self.hash_to_file.get(key)
        if isinstance(key, str):
            return self.name_to_files.get(key, [])
        if isinstance(key, Path):
            return self.path_to_file.get(key)
        return None

    def remove(self, key):
        """Remove a file from the index."""
        if isinstance(key, int):
            file = self.hash_to_file.pop(key, None)
            if file:
                self.files.remove(file)
                self.name_to_files[file.path.name].remove(file)
                if not self.name_to_files[file.path.name]:
                    del self.name_to_files[file.path.name]
                del self.path_to_file[file.file_path]
        elif isinstance(key, str):
            files = self.name_to_files.pop(key, [])
            for file in files:
                self.files.remove(file)
                del self.hash_to_file[file]
                del self.path_to_file[file.file_path]
        elif isinstance(key, Path):
            file = self.path_to_file.pop(key, None)
            if file:
                self.files.remove(file)
                del self.hash_to_file[file]
                self.name_to_files[file.path.name].remove(file)
                if not self.name_to_files[file.path.name]:
                    del self.name_to_files[file.path.name]
