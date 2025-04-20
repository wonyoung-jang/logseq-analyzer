"""
Query Graph Module.
"""

from typing import Generator, List

from ..logseq_file.file import LogseqFile
from ..utils.helpers import singleton
from .index import FileIndex


@singleton
class Query:
    """
    Class to query the Logseq graph for specific file attributes.
    """

    def list_files_with_keys_and_values(self, **criteria) -> List[LogseqFile]:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for file in FileIndex().files:
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file)
        return result

    def list_file_names_with_keys_and_values(self, **criteria) -> list:
        """Extract a subset of the summary data based on multiple criteria (key-value pairs)."""
        result = []
        for file in FileIndex().files:
            if all(getattr(file, key) == expected for key, expected in criteria.items()):
                result.append(file.path.name)
        return result

    def yield_files_with_keys(self, *criteria) -> Generator[LogseqFile, None, None]:
        """Extract a subset of the summary data based on whether the keys exists."""
        for file in FileIndex().files:
            if all(hasattr(file, key) for key in criteria):
                yield file

    def list_files_without_keys(self, *criteria) -> List[str]:
        """Extract a subset of the summary data based on whether the keys do not exist."""
        result = []
        for file in FileIndex().files:
            if all(not hasattr(file, key) for key in criteria):
                result.append(file.path.name)
        return result
