"""File system operations for Logseq Analyzer."""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..utils.enums import Constant, DirsAnalyzer, DirsDelete, DirsGraph

logger = logging.getLogger(__name__)

__all__ = [
    "AnalyzerDeleteDirs",
    "AssetsDirectory",
    "BakDirectory",
    "CacheFile",
    "ConfigFile",
    "DeleteAssetsDirectory",
    "DeleteBakDirectory",
    "DeleteDirectory",
    "DeleteRecycleDirectory",
    "DrawsDirectory",
    "File",
    "GlobalConfigFile",
    "GraphDirectory",
    "JournalsDirectory",
    "LogFile",
    "LogseqAnalyzerDirs",
    "LogseqDirectory",
    "LogseqGraphDirs",
    "OutputDirectory",
    "PagesDirectory",
    "RecycleDirectory",
    "WhiteboardsDirectory",
]


@dataclass(slots=True)
class File:
    """A class to represent a file in the Logseq Analyzer."""

    path: Path

    clean_on_init: bool = False
    must_exist: bool = False
    is_dir: bool = False

    def __post_init__(self) -> None:
        """Initialize the File class with a path."""
        if not isinstance(self.path, Path):
            self.path = Path(self.path)
        self.startup()
        logger.info("File initialized: %s", self.path)

    def startup(self) -> None:
        """Perform startup operations for the File object."""
        if self.must_exist:
            self.validate()
        if self.clean_on_init and self.path.exists():
            self.clean()
        self.make_if_missing()
        if not (self.must_exist or self.clean_on_init):
            self.validate()

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


@dataclass(slots=True)
class OutputDirectory(File):
    """Class to handle the output directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for OutputDirectory."""
        self.clean_on_init = True
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class LogFile(File):
    """Class to handle the log file for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for LogFile."""
        return super().__post_init__()


@dataclass(slots=True)
class GraphDirectory(File):
    """Class to handle the graph directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for GraphDirectory."""
        self.must_exist = True
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class LogseqDirectory(File):
    """Class to handle the Logseq directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for LogseqDirectory."""
        self.must_exist = True
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class ConfigFile(File):
    """Class to handle the config file for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for ConfigFile."""
        self.must_exist = True
        return super().__post_init__()


@dataclass(slots=True)
class DeleteDirectory(File):
    """Class to handle the delete directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for DeleteDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class DeleteBakDirectory(File):
    """Class to handle the delete bak directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for DeleteBakDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class DeleteRecycleDirectory(File):
    """Class to handle the delete recycle directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for DeleteRecycleDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class DeleteAssetsDirectory(File):
    """Class to handle the delete assets directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for DeleteAssetsDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class CacheFile(File):
    """Class to handle the cache file for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for CacheFile."""
        return super().__post_init__()


@dataclass(slots=True)
class BakDirectory(File):
    """Class to handle the bak directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for BakDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class RecycleDirectory(File):
    """Class to handle the recycle directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for RecycleDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class GlobalConfigFile(File):
    """Class to handle the global config file for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for GlobalConfigFile."""
        self.must_exist = True
        return super().__post_init__()


@dataclass(slots=True)
class AssetsDirectory(File):
    """Class to handle the assets directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for AssetsDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class DrawsDirectory(File):
    """Class to handle the draws directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for DrawsDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class JournalsDirectory(File):
    """Class to handle the journals directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for JournalsDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class PagesDirectory(File):
    """Class to handle the pages directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for PagesDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class WhiteboardsDirectory(File):
    """Class to handle the whiteboards directory for the Logseq Analyzer."""

    def __post_init__(self) -> None:
        """Post-initialization for WhiteboardsDirectory."""
        self.is_dir = True
        return super().__post_init__()


@dataclass(slots=True)
class LogseqGraphDirs:
    """Directories related to the Logseq graph."""

    graph_dir: GraphDirectory
    logseq_dir: LogseqDirectory
    bak_dir: BakDirectory
    recycle_dir: RecycleDirectory
    user_config: ConfigFile
    global_config: GlobalConfigFile | None = None

    @property
    def report(self) -> dict[DirsGraph, Any]:
        """Generate a report of the Logseq graph directories."""
        return {
            DirsGraph.GRAPH: self.graph_dir,
            DirsGraph.LOGSEQ: self.logseq_dir,
            DirsGraph.BAK: self.bak_dir,
            DirsGraph.RECYCLE: self.recycle_dir,
            DirsGraph.USER_CONFIG: self.user_config,
            DirsGraph.GLOBAL_CONFIG: self.global_config,
        }


@dataclass(slots=True)
class AnalyzerDeleteDirs:
    """Directories for deletion operations in the Logseq analyzer."""

    delete_dir: DeleteDirectory | None = None
    delete_bak_dir: DeleteBakDirectory | None = None
    delete_recycle_dir: DeleteRecycleDirectory | None = None
    delete_assets_dir: DeleteAssetsDirectory | None = None

    def __post_init__(self) -> None:
        """Initialize the AnalyzerDeleteDirs class."""
        self.delete_dir = DeleteDirectory(Path(Constant.TO_DELETE_DIR))
        self.delete_bak_dir = DeleteBakDirectory(Path(Constant.TO_DELETE_BAK_DIR))
        self.delete_recycle_dir = DeleteRecycleDirectory(Path(Constant.TO_DELETE_RECYCLE_DIR))
        self.delete_assets_dir = DeleteAssetsDirectory(Path(Constant.TO_DELETE_ASSETS_DIR))

    @property
    def report(self) -> dict[DirsDelete, Any]:
        """Generate a report of the analyzer delete directories."""
        return {
            DirsDelete.DELETE: self.delete_dir,
            DirsDelete.BAK: self.delete_bak_dir,
            DirsDelete.RECYCLE: self.delete_recycle_dir,
            DirsDelete.ASSETS: self.delete_assets_dir,
        }


@dataclass(slots=True)
class LogseqAnalyzerDirs:
    """Directories used by the Logseq analyzer."""

    graph_dirs: LogseqGraphDirs
    delete_dirs: AnalyzerDeleteDirs
    target_dirs: dict[str, str]
    output_dir: OutputDirectory

    @property
    def report(self) -> dict[DirsAnalyzer, dict[DirsAnalyzer, Any]]:
        """Generate a report of the Logseq analyzer directories."""
        return {
            DirsAnalyzer.DIRS: {
                DirsAnalyzer.GRAPH: self.graph_dirs.report,
                DirsAnalyzer.DELETE: self.delete_dirs.report,
                DirsAnalyzer.TARGET: self.target_dirs,
                DirsAnalyzer.OUTPUT: self.output_dir,
            }
        }
