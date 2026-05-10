"""File system operations for Logseq Analyzer."""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from logseq_analyzer.utils.enums import OutputDir

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


@dataclass(slots=True)
class LogseqAnalyzerDirs:
    """Directories used by the Logseq analyzer."""

    graph: File
    logseq: File
    bak: File
    recycle: File
    config_user: File
    del_directory: File
    del_bak: File
    del_recycle: File
    del_assets: File
    target: dict[str, str]
    output: File
    config_global: File | None = None

    @property
    def report(self) -> dict[str, dict]:
        """Generate a report of the Logseq analyzer directories."""
        return {
            OutputDir.META: {
                "logseq_analyzer_dirs": {
                    "graph_dirs": {
                        "graph": self.graph,
                        "graph/logseq": self.logseq,
                        "graph/logseq/bak": self.bak,
                        "graph/logseq/.recycle": self.recycle,
                        "graph/logseq/config.edn": self.config_user,
                        "global-config.edn": self.config_global,
                    },
                    "delete_dirs": {
                        "to-delete": self.del_directory,
                        "to-delete/bak": self.del_bak,
                        "to-delete/.recycle": self.del_recycle,
                        "to-delete/assets": self.del_assets,
                    },
                    "target_dirs": self.target,
                    "output_dir": self.output,
                }
            }
        }
