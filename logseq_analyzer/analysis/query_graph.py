"""
Query Graph Module.
"""

from ..utils.helpers import singleton
from ..logseq_file.file import LogseqFile
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
        return self.graph.name_to_hashes_map.get(name)

    def hash_to_file(self, hash_: int):
        """Get a Logseq file by its hash."""
        return self.graph.hash_to_file_map.get(hash_)

    def name_to_files(self, name: str):
        """Get Logseq files by name."""
        files = []
        if hashes := self.name_to_hashes(name):
            for hash_ in hashes:
                if file := self.hash_to_file(hash_):
                    files.append(file)
        return files

    def hash_to_name(self, hash_: int):
        """Get a Logseq file name by its hash."""
        if hash_ not in self.graph.hash_to_file_map:
            return None
        return self.graph.hash_to_file_map[hash_].path.name

    def file_to_hash(self, file: LogseqFile):
        """Get the hash of a Logseq file."""
        return hash(file)

    def file_to_name(self, file: LogseqFile):
        """Get the name of a Logseq file."""
        return file.path.name

    def list_files_with_keys_and_values(self, **criteria) -> list:
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
