"""
FileIndex class.
"""

from dataclasses import dataclass, field
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, ClassVar, Iterator

from ..logseq_file.file import LogseqFile
from ..utils.enums import Output
from ..utils.helpers import yield_attrs

logger = logging.getLogger(__name__)


__all__ = [
    "FileIndex",
]


@dataclass(slots=True)
class FileIndex:
    """Class to index files in the Logseq graph."""

    _instance: ClassVar["FileIndex"] = None
    write_graph: ClassVar[bool] = False

    _files: set[LogseqFile] = field(default_factory=set)
    _name_to_files: dict[str, list[LogseqFile]] = field(default_factory=lambda: defaultdict(list))
    _path_to_file: dict[Path, LogseqFile] = field(default_factory=dict)

    def __new__(cls) -> "FileIndex":
        """Ensure only one instance of FileIndex is created."""
        if cls._instance is None:
            cls._instance = super(FileIndex, cls).__new__(cls)
        return cls._instance

    def __len__(self) -> int:
        """Return the number of files in the index."""
        return len(self._files)

    def __iter__(self) -> Iterator[LogseqFile]:
        """Iterate over the files in the index."""
        return iter(self._files)

    def __getitem__(self, f: Any) -> Any:
        """Get a file by its key."""
        if isinstance(f, LogseqFile):
            if f in self:
                return f
            raise KeyError(f"File {f} not found in index.")
        if isinstance(f, str):
            return self._name_to_files.get(f, [])
        if isinstance(f, Path):
            return self._path_to_file.get(f)
        raise TypeError(f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path.")

    def __contains__(self, f: Any) -> bool:
        """Check if a file is in the index."""
        if isinstance(f, LogseqFile):
            return f in self._files
        if isinstance(f, str):
            return f in self._name_to_files
        if isinstance(f, Path):
            return f in self._path_to_file
        raise TypeError(f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path.")

    def add(self, f: LogseqFile) -> None:
        """Add a file to the index."""
        self._files.add(f)
        self._name_to_files[f.path.name].append(f)
        self._path_to_file[f.path.file] = f

    def remove(self, f: Any) -> None:
        """Strategy to remove a file from the index."""
        if isinstance(f, LogseqFile):
            target = f
        elif isinstance(f, str):
            for target in self._name_to_files.pop(f, []):
                self._remove_file(target)
            return
        elif isinstance(f, Path):
            target = self._path_to_file.get(f)
        else:
            raise TypeError(f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path.")

        if target is None:
            logging.warning("Key %s not found in index.", f)
            return
        self._remove_file(target)
        logger.debug("Key %s removed from index.", f)

    def _remove_file(self, f: LogseqFile) -> None:
        """Helper method to remove a file from the index."""
        self._files.discard(f)
        if files := self._name_to_files.get(f.path.name):
            try:
                files.remove(f)
            except ValueError:
                logger.warning("File %s not found in name_to_files list for name %s.", f, f.path.name)
        else:
            del self._name_to_files[f.path.name]
        self._path_to_file.pop(f.path.file, None)

    def remove_deleted_files(self) -> None:
        """Remove deleted files from the cache."""
        if not self:
            return

        for file in {f for f in self if not f.path.file.exists()}:
            self.remove(file)

    @property
    def graph_data(self) -> dict[LogseqFile, dict[str, Any]]:
        """Get metadata file data from the graph."""
        return {file: {k: v for k, v in yield_attrs(file) if v and k not in ("data", "masked")} for file in self}

    @property
    def graph_content_data(self) -> dict[LogseqFile, Any]:
        """Get content data from the graph."""
        return {file: {k: v for k, v in file.data.items() if v} for file in self}

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the indexed files."""
        report = {
            Output.GRAPH_CONTENT_DATA: self.graph_content_data,
            Output.GRAPH_DATA: self.graph_data,
            Output.IDX_FILES: self._files,
            Output.IDX_NAME_TO_FILES: self._name_to_files,
            Output.IDX_PATH_TO_FILE: self._path_to_file,
        }
        if FileIndex.write_graph:
            report[Output.GRAPH_CONTENT] = {f: f.bullets.content for f in self}
            report[Output.GRAPH_BULLETS] = {f: f.bullets.all_bullets for f in self}
        return report
