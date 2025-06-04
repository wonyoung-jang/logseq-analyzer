"""
File system operations for Logseq Analyzer.
"""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class File:
    """A class to represent a file in the Logseq Analyzer."""

    __slots__ = ("_path",)

    clean_on_init: bool = False
    must_exist: bool = False
    is_dir: bool = False

    def __init__(self, path: Path) -> None:
        """Initialize the File class with a path."""
        self.path: Path = path
        self.startup()
        logger.info("File initialized: %s", self.path)

    def __repr__(self) -> str:
        """Return a string representation of the File object."""
        return f'{self.__class__.__qualname__}(path="{str(self.path)}")'

    def __str__(self) -> str:
        """Return a string representation of the File object."""
        return f"{self.__class__.__qualname__}: {str(self.path)}"

    @property
    def path(self) -> Path:
        """Get the path of the file."""
        return self._path

    @path.setter
    def path(self, value: str | Path) -> None:
        """Set the path of the file."""
        if isinstance(value, str):
            value = Path(value)
        self._path = value

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
            raise FileNotFoundError(f"File does not exist: {self.path}")
        if self.is_dir and not self.path.is_dir():
            logger.error("Path is not a directory: %s", self.path)
            raise NotADirectoryError(f"Path is not a directory: {self.path}")
        if not self.is_dir and not self.path.is_file():
            logger.error("Path is not a file: %s", self.path)
            raise FileNotFoundError(f"Path is not a file: {self.path}")
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
            logger.error("Permission denied to delete path: %s", self.path)
        except OSError as e:
            logger.error("Error deleting path: %s", e)

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
            logger.error("Permission denied to create path: %s", self.path)
        except OSError as e:
            logger.error("Error creating path: %s", e)


class OutputDirectory(File):
    """Class to handle the output directory for the Logseq Analyzer."""

    clean_on_init = True
    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnaly zerOutputDir class."""
        super().__init__(path)


class LogFile(File):
    """Class to handle the log file for the Logseq Analyzer."""

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerLogFile class."""
        super().__init__(path)


class GraphDirectory(File):
    """Class to handle the graph directory for the Logseq Analyzer."""

    must_exist = True
    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerGraphDir class."""
        super().__init__(path)


class LogseqDirectory(File):
    """Class to handle the Logseq directory for the Logseq Analyzer."""

    must_exist = True
    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerLogseqDir class."""
        super().__init__(path)


class ConfigFile(File):
    """Class to handle the config file for the Logseq Analyzer."""

    must_exist = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerConfigFile class."""
        super().__init__(path)


class DeleteDirectory(File):
    """Class to handle the delete directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerDeleteDir class."""
        super().__init__(path)


class DeleteBakDirectory(File):
    """Class to handle the delete bak directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerDeleteBakDir class."""
        super().__init__(path)


class DeleteRecycleDirectory(File):
    """Class to handle the delete recycle directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerDeleteRecycleDir class."""
        super().__init__(path)


class DeleteAssetsDirectory(File):
    """Class to handle the delete assets directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerDeleteAssetsDir class."""
        super().__init__(path)


class CacheFile(File):
    """Class to handle the cache file for the Logseq Analyzer."""

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerCacheFile class."""
        super().__init__(path)


class BakDirectory(File):
    """Class to handle the bak directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerBakDir class."""
        super().__init__(path)


class RecycleDirectory(File):
    """Class to handle the recycle directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerRecycleDir class."""
        super().__init__(path)


class GlobalConfigFile(File):
    """Class to handle the global config file for the Logseq Analyzer."""

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerGlobalConfigFile class."""
        super().__init__(path)


class AssetsDirectory(File):
    """Class to handle the assets directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerAssetsDir class."""
        super().__init__(path)


class DrawsDirectory(File):
    """Class to handle the draws directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerDrawsDir class."""
        super().__init__(path)


class JournalsDirectory(File):
    """Class to handle the journals directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerJournalsDir class."""
        super().__init__(path)


class PagesDirectory(File):
    """Class to handle the pages directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerPagesDir class."""
        super().__init__(path)


class WhiteboardsDirectory(File):
    """Class to handle the whiteboards directory for the Logseq Analyzer."""

    is_dir = True

    def __init__(self, path: str | Path = None) -> None:
        """Initialize the LogseqAnalyzerWhiteboardsDir class."""
        super().__init__(path)
