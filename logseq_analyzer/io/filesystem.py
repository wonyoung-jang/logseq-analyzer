"""File system operations for Logseq Analyzer."""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class File:
    """A class to represent a file in the Logseq Analyzer."""

    path: Path
    clean_on_init: bool = False
    must_exist: bool = False
    is_dir: bool = False
    create: bool = True

    def __post_init__(self) -> None:
        """Initialize the File class with a path."""
        if not isinstance(self.path, Path):
            self.path = Path(self.path)
        if self.must_exist:
            self.validate()
        if self.clean_on_init and self.path.exists():
            self.clean()
        if self.create:
            self.make_if_missing()
        logger.info("File initialized: %s", self.path)

    def validate(self) -> None:
        """Validate the file path."""
        if not self.path.exists():
            logger.error("File does not exist: %s", self.path)
            msg = f"File does not exist: {self.path}"
            raise FileNotFoundError(msg)
        if self.is_dir and not self.path.is_dir():
            logger.error("Path is not a directory: %s", self.path)
            msg = f"Path is not a directory: {self.path}"
            raise NotADirectoryError(msg)
        if not self.is_dir and not self.path.is_file():
            logger.error("Path is not a file: %s", self.path)
            msg = f"Path is not a file: {self.path}"
            raise FileNotFoundError(msg)
        logger.info("%s exists", self.path)

    def clean(self) -> None:
        """Clean up the file or directory."""
        try:
            if self.is_dir:
                shutil.rmtree(self.path)
                logger.info("Deleted directory: %s", self.path)
            else:
                self.path.unlink()
                logger.info("Deleted file: %s", self.path)
        except PermissionError:
            logger.exception("Permission denied to delete path: %s", self.path)
        except OSError:
            logger.exception("Error deleting path")

    def make_if_missing(self) -> None:
        """Create the file or directory if it does not exist."""
        try:
            if not self.path.exists():
                if self.is_dir:
                    self.path.mkdir(parents=True, exist_ok=True)
                    logger.info("Created directory: %s", self.path)
                else:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    self.path.touch(exist_ok=True)
                    logger.info("Created file: %s", self.path)
        except PermissionError:
            logger.exception("Permission denied to create path: %s", self.path)
        except OSError:
            logger.exception("Error creating path")


def _file_cls(
    name: str, *, is_dir: bool = False, must_exist: bool = False, clean_on_init: bool = False, create: bool = True
) -> type[File]:
    """File subclass with preset flags."""

    class _C(File):
        def __post_init__(self) -> None:
            self.is_dir = is_dir
            self.must_exist = must_exist
            self.clean_on_init = clean_on_init
            self.create = create
            super().__post_init__()

    _C.__name__ = _C.__qualname__ = name
    return _C


# fmt: off
OutputDirectory         = _file_cls("OutputDirectory",         is_dir=True, clean_on_init=True)
LogFile                 = _file_cls("LogFile")
GraphDirectory          = _file_cls("GraphDirectory",          is_dir=True, must_exist=True)
LogseqDirectory         = _file_cls("LogseqDirectory",         is_dir=True, must_exist=True)
ConfigFile              = _file_cls("ConfigFile",              must_exist=True)
GlobalConfigFile        = _file_cls("GlobalConfigFile",        must_exist=True)
CacheFile               = _file_cls("CacheFile",               create=False)
BakDirectory            = _file_cls("BakDirectory",            is_dir=True)
RecycleDirectory        = _file_cls("RecycleDirectory",        is_dir=True)
AssetsDirectory         = _file_cls("AssetsDirectory",         is_dir=True)
DrawsDirectory          = _file_cls("DrawsDirectory",          is_dir=True)
JournalsDirectory       = _file_cls("JournalsDirectory",       is_dir=True)
PagesDirectory          = _file_cls("PagesDirectory",          is_dir=True)
WhiteboardsDirectory    = _file_cls("WhiteboardsDirectory",    is_dir=True)
DeleteDirectory         = _file_cls("DeleteDirectory",         is_dir=True)
DeleteBakDirectory      = _file_cls("DeleteBakDirectory",      is_dir=True)
DeleteRecycleDirectory  = _file_cls("DeleteRecycleDirectory",  is_dir=True)
DeleteAssetsDirectory   = _file_cls("DeleteAssetsDirectory",   is_dir=True)
# fmt: on


@dataclass(slots=True)
class LogseqGraphDirs:
    """Directories related to the Logseq graph."""

    graph: File
    logseq: File
    bak: File
    recycle: File
    config_user: File
    config_global: File | None = None


@dataclass(slots=True)
class AnalyzerDeleteDirs:
    """Directories for deletion operations in the Logseq analyzer."""

    directory: File
    bak: File
    recycle: File
    assets: File


@dataclass(slots=True)
class LogseqAnalyzerDirs:
    """Directories used by the Logseq analyzer."""

    graph: LogseqGraphDirs
    delete: AnalyzerDeleteDirs
    target: dict[str, str]
    output: File

    @property
    def report(self) -> dict[str, dict]:
        """Generate a report of the Logseq analyzer directories."""
        return {
            "logseq_analyzer_dirs": {
                "graph_dirs": {
                    "graph": self.graph.graph,
                    "graph/logseq": self.graph.logseq,
                    "graph/logseq/bak": self.graph.bak,
                    "graph/logseq/.recycle": self.graph.recycle,
                    "graph/logseq/config.edn": self.graph.config_user,
                    "global-config.edn": self.graph.config_global,
                },
                "delete_dirs": {
                    "to-delete": self.delete.directory,
                    "to-delete/bak": self.delete.bak,
                    "to-delete/.recycle": self.delete.recycle,
                    "to-delete/assets": self.delete.assets,
                },
                "target_dirs": self.target,
                "output_dir": self.output,
            }
        }
