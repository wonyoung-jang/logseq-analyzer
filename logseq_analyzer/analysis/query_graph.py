"""
Query Graph Module.
"""

from typing import Generator, List

from ..logseq_file.file import LogseqFile
from ..logseq_file.name import LogseqFilename
from ..utils.helpers import singleton
from .graph import LogseqGraph


@singleton
class Query:
    """
    Class to query the Logseq graph for specific file attributes.
    """

    def __init__(self):
        """Initialize the Query class with a LogseqGraph instance."""
        self.graph = LogseqGraph()

    def name_to_hashes(self, name: str):
        """Get a Logseq file by its name."""
        return self.graph.name_to_hashes_map.get(name, [])

    def hash_to_file(self, hash_: int):
        """Get a Logseq file by its hash."""
        return self.graph.hash_to_file_map.get(hash_, None)

    def name_to_files(self, name: str):
        """Get Logseq files by name."""
        return self.graph.name_to_files_map.get(name, [])

    def hash_to_name(self, hash_: int):
        """Get a Logseq file name by its hash."""
        if not (path := self.graph.hash_to_file_map.get(hash_)):
            return None
        return path.path.name

    def file_to_hash(self, file: LogseqFile):
        """Get the hash of a Logseq file."""
        return hash(file)

    def file_to_name(self, file: LogseqFile):
        """Get the name of a Logseq file."""
        return file.path.name

    def list_files_with_keys_and_values(self, **criteria) -> List[LogseqFile]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for _, file in self.graph.hash_to_file_map.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file)
        return result

    def list_file_names_with_keys_and_values(self, **criteria) -> list:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for _, file in self.graph.hash_to_file_map.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.path.name)
        return result

    def yield_files_with_keys(self, *criteria) -> Generator[LogseqFilename, None, None]:
        """Extract a subset of the summary data based on whether the keys exists."""
        for _, file in self.graph.hash_to_file_map.items():
            if all(hasattr(file, key) for key in criteria):
                yield file

    def list_files_without_keys(self, *criteria) -> List[str]:
        """Extract a subset of the summary data based on whether the keys do not exist."""
        result = []
        for _, file in self.graph.hash_to_file_map.items():
            if all(not hasattr(file, key) for key in criteria):
                result.append(file.path.name)
        return result
