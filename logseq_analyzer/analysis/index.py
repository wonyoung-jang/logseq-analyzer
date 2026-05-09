"""FileIndex class."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from logseq_analyzer.analysis.file import LogseqFile
from logseq_analyzer.utils.enums import FileType, Output

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FileIndex:
    """Class to index files in the Logseq graph."""

    _files: set[LogseqFile] = field(default_factory=set)
    _name_to_files: dict[str, list[LogseqFile]] = field(default_factory=lambda: defaultdict(list))
    _path_to_file: dict[Path, LogseqFile] = field(default_factory=dict)
    write_graph: bool = field(init=False, default=False)

    def __len__(self) -> int:
        """Return the number of files in the index."""
        return len(self._files)

    def __iter__(self) -> Iterator[LogseqFile]:
        """Iterate over the files in the index."""
        return iter(self._files)

    def __getitem__(self, f: Any) -> LogseqFile | list[LogseqFile] | None:
        """Get a file by its key."""
        if isinstance(f, LogseqFile):
            if f in self:
                return f
            msg = f"File {f} not found in index."
            raise KeyError(msg)
        if isinstance(f, str):
            return self._name_to_files.get(f, [])
        if isinstance(f, Path):
            return self._path_to_file.get(f)
        msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path."
        raise TypeError(msg)

    def __contains__(self, f: Any) -> bool:
        """Check if a file is in the index."""
        if isinstance(f, LogseqFile):
            return f in self._files
        if isinstance(f, str):
            return f in self._name_to_files
        if isinstance(f, Path):
            return f in self._path_to_file
        msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path."
        raise TypeError(msg)

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
            msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path."
            raise TypeError(msg)
        if target is None:
            logger.warning("Key %s not found in index.", f)
            return
        self._remove_file(target)
        logger.debug("Key %s removed from index.", f)

    def _remove_file(self, f: LogseqFile) -> None:
        """Remove a file from the index."""
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
        for f in self:
            if not f.path.file.exists():
                self.remove(f)

    def yield_names(self) -> Iterator[str]:
        """Yield all file names from the index."""
        yield from (f.path.name for f in self)

    def yield_non_ns_names(self) -> Iterator[str]:
        """Yield all non-namespace file names from the index."""
        yield from (f.path.name for f in self if not f.info.namespace.is_namespace)

    def yield_journals(self) -> Iterator[str]:
        """Yield all journal files from the index."""
        yield from (f.path.name for f in self if f.path.file_type == FileType.JOURNAL)

    def yield_assets_with_backlink(self, *, backlinked: bool) -> Iterator[LogseqFile]:
        """Yield asset files with or without backlinks."""
        for f in self:
            if (backlinked or f.node.backlinked == backlinked) and f.path.file_type == FileType.ASSET:
                yield f

    @property
    def graph_data(self) -> dict[LogseqFile, dict[str, Any]]:
        """Get metadata file data from the graph."""
        return {file: {k: v for k, v in file.yield_attrs() if v} for file in self}

    @property
    def graph_content_data(self) -> dict[LogseqFile, Any]:
        """Get content data from the graph."""
        return {file: {k: v for k, v in file.data.items() if v} for file in self}

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the indexed files."""
        _report: dict[str, Any] = {
            Output.GRAPH_CONTENT_DATA: self.graph_content_data,
            Output.GRAPH_DATA: self.graph_data,
            Output.IDX_FILES: self._files,
            Output.IDX_NAME_TO_FILES: self._name_to_files,
            Output.IDX_PATH_TO_FILE: self._path_to_file,
        }
        if self.write_graph:
            _report[Output.GRAPH_CONTENT] = {f: f.bullets.content for f in self}
            _report[Output.GRAPH_BULLETS] = {f: f.bullets.all_bullets for f in self}
        return _report
