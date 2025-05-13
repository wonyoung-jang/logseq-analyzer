"""
File system operations for Logseq Analyzer.
"""

import logging
import shutil
from pathlib import Path

from ..config.analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import singleton


class File:
    """A class to represent a file in the Logseq Analyzer."""

    __slots__ = ("_path",)

    config = LogseqAnalyzerConfig()

    def __init__(self, path: Path) -> None:
        """Initialize the File class with a path."""
        self.path = path

    def __repr__(self) -> str:
        """Return a string representation of the File object."""
        return f'File(path="{str(self.path)}")'

    def __str__(self) -> str:
        """Return a string representation of the File object."""
        return f"File: {str(self.path)}"

    # Getter for path property
    @property
    def path(self) -> Path:
        """Get the path of the file."""
        return self._path

    # Setter for path property
    @path.setter
    def path(self, value: str | Path) -> None:
        """Set the path of the file."""
        if isinstance(value, str):
            value = Path(value)
        self._path = value

    def validate(self) -> None:
        """Validate the file path."""
        if not self.path.exists():
            logging.error("File does not exist: %s", self.path)
            raise FileNotFoundError(f"File does not exist: {self.path}")
        logging.info("File exists: %s", self.path)

    def get_or_create_dir(self) -> None:
        """Get a path or create it if it doesn't exist."""
        try:
            self.path.resolve(strict=True)
            logging.info("Path exists: %s", self.path)
        except FileNotFoundError:
            try:
                self.path.mkdir(parents=True, exist_ok=True)
                logging.info("Created path: %s", self.path)
            except PermissionError:
                logging.error("Permission denied to create path: %s", self.path)
            except OSError as e:
                logging.error("Error creating path: %s", e)

    def get_or_create_file(self) -> None:
        """Get a path or create it if it doesn't exist."""
        try:
            self.path.resolve(strict=True)
            logging.info("Path exists: %s", self.path)
        except FileNotFoundError:
            try:
                self.path.touch(exist_ok=True)
                logging.info("Created file: %s", self.path)
            except PermissionError:
                logging.error("Permission denied to create path: %s", self.path)
            except OSError as e:
                logging.error("Error creating path: %s", e)

    def initialize_dir(self) -> None:
        """Initialize the directory."""
        try:
            if self.path.exists():
                shutil.rmtree(self.path)
                logging.info("Deleted path: %s", self.path)
        except PermissionError:
            logging.error("Permission denied to delete path: %s", self.path)
        except OSError as e:
            logging.error("Error deleting path: %s", e)
        finally:
            self.get_or_create_dir()
            logging.info("Created path: %s", self.path)

    def initialize_file(self) -> None:
        """Initialize the file or directory."""
        try:
            if self.path.exists():
                self.path.unlink()
                logging.info("Deleted path: %s", self.path)
        except PermissionError:
            logging.error("Permission denied to delete path: %s", self.path)
        except OSError as e:
            logging.error("Error deleting path: %s", e)
        finally:
            self.get_or_create_file()
            logging.info("Created path: %s", self.path)


@singleton
class OutputDirectory(File):
    """Class to handle the output directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerOutputDir class."""
        super().__init__(File.config.get("CONST", "OUTPUT_DIR"))


@singleton
class LogFile(File):
    """Class to handle the log file for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerLogFile class."""
        super().__init__(File.config.get("CONST", "LOG_FILE"))


@singleton
class GraphDirectory(File):
    """Class to handle the graph directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerGraphDir class."""
        super().__init__(File.config.get("ANALYZER", "GRAPH_DIR"))


@singleton
class LogseqDirectory(File):
    """Class to handle the Logseq directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerLogseqDir class."""
        super().__init__(File.config.get("CONST", "LOGSEQ_DIR"))


@singleton
class ConfigFile(File):
    """Class to handle the config file for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerConfigFile class."""
        super().__init__(File.config.get("CONST", "CONFIG_FILE"))


@singleton
class DeleteDirectory(File):
    """Class to handle the delete directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerDeleteDir class."""
        super().__init__(File.config.get("CONST", "TO_DELETE_DIR"))


@singleton
class DeleteBakDirectory(File):
    """Class to handle the delete bak directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerDeleteBakDir class."""
        super().__init__(File.config.get("CONST", "TO_DELETE_BAK_DIR"))


@singleton
class DeleteRecycleDirectory(File):
    """Class to handle the delete recycle directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerDeleteRecycleDir class."""
        super().__init__(File.config.get("CONST", "TO_DELETE_RECYCLE_DIR"))


@singleton
class DeleteAssetsDirectory(File):
    """Class to handle the delete assets directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerDeleteAssetsDir class."""
        super().__init__(File.config.get("CONST", "TO_DELETE_ASSETS_DIR"))


@singleton
class CacheFile(File):
    """Class to handle the cache file for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerCacheFile class."""
        super().__init__(File.config.get("CONST", "CACHE"))


@singleton
class BakDirectory(File):
    """Class to handle the bak directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerBakDir class."""
        super().__init__(File.config.get("CONST", "BAK_DIR"))


@singleton
class RecycleDirectory(File):
    """Class to handle the recycle directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerRecycleDir class."""
        super().__init__(File.config.get("CONST", "RECYCLE_DIR"))


@singleton
class GlobalConfigFile(File):
    """Class to handle the global config file for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerGlobalConfigFile class."""
        super().__init__(File.config.get("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE"))


@singleton
class AssetsDirectory(File):
    """Class to handle the assets directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerAssetsDir class."""
        super().__init__(File.config.get("TARGET_DIRS", "DIR_ASSETS"))


@singleton
class DrawsDirectory(File):
    """Class to handle the draws directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerDrawsDir class."""
        super().__init__(File.config.get("TARGET_DIRS", "DIR_DRAWS"))


@singleton
class JournalsDirectory(File):
    """Class to handle the journals directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerJournalsDir class."""
        super().__init__(File.config.get("TARGET_DIRS", "DIR_JOURNALS"))


@singleton
class PagesDirectory(File):
    """Class to handle the pages directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerPagesDir class."""
        super().__init__(File.config.get("TARGET_DIRS", "DIR_PAGES"))


@singleton
class WhiteboardsDirectory(File):
    """Class to handle the whiteboards directory for the Logseq Analyzer."""

    def __init__(self) -> None:
        """Initialize the LogseqAnalyzerWhiteboardsDir class."""
        super().__init__(File.config.get("TARGET_DIRS", "DIR_WHITEBOARDS"))
