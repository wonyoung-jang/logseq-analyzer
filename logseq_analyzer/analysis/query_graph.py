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

    def list_files_with_keys_and_values(self, **criteria) -> List[LogseqFile]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for _, file in self.graph.index.hash_to_file.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file)
        return result

    def list_file_names_with_keys_and_values(self, **criteria) -> list:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for _, file in self.graph.index.hash_to_file.items():
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.path.name)
        return result

    def yield_files_with_keys(self, *criteria) -> Generator[LogseqFilename, None, None]:
        """Extract a subset of the summary data based on whether the keys exists."""
        for _, file in self.graph.index.hash_to_file.items():
            if all(hasattr(file, key) for key in criteria):
                yield file

    def list_files_without_keys(self, *criteria) -> List[str]:
        """Extract a subset of the summary data based on whether the keys do not exist."""
        result = []
        for _, file in self.graph.index.hash_to_file.items():
            if all(not hasattr(file, key) for key in criteria):
                result.append(file.path.name)
        return result
