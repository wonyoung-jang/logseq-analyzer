"""
File system operations for Logseq Analyzer.
"""

import logging
import shutil
from pathlib import Path

from ..utils.enums import Constants
from ..utils.helpers import singleton


class File:
    """A class to represent a file in the Logseq Analyzer."""

    __slots__ = ("_path",)

    def __init__(self, path: Path) -> None:
        """Initialize the File class with a path."""
        self.path = path
        logging.info("File initialized: %s", self.path)

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
class ConfigIniFile(File):
    """Class to handle the config.ini file for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.CONFIG_INI_FILE.value) -> None:
        """Initialize the LogseqAnalyzerConfigIniFile class."""
        super().__init__(path)


@singleton
class UserConfigIniFile(File):
    """Class to handle the user_config.ini file for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.CONFIG_USER_INI_FILE.value) -> None:
        """Initialize the LogseqAnalyzerUserConfigIniFile class."""
        super().__init__(path)


@singleton
class OutputDirectory(File):
    """Class to handle the output directory for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.OUTPUT_DIR.value) -> None:
        """Initialize the LogseqAnalyzerOutputDir class."""
        super().__init__(path)


@singleton
class LogFile(File):
    """Class to handle the log file for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.LOG_FILE.value) -> None:
        """Initialize the LogseqAnalyzerLogFile class."""
        super().__init__(path)


@singleton
class GraphDirectory(File):
    """Class to handle the graph directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerGraphDir class."""
        super().__init__(path)


@singleton
class LogseqDirectory(File):
    """Class to handle the Logseq directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerLogseqDir class."""
        super().__init__(path)


@singleton
class ConfigFile(File):
    """Class to handle the config file for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerConfigFile class."""
        super().__init__(path)


@singleton
class DeleteDirectory(File):
    """Class to handle the delete directory for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.TO_DELETE_DIR.value) -> None:
        """Initialize the LogseqAnalyzerDeleteDir class."""
        super().__init__(path)


@singleton
class DeleteBakDirectory(File):
    """Class to handle the delete bak directory for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.TO_DELETE_BAK_DIR.value) -> None:
        """Initialize the LogseqAnalyzerDeleteBakDir class."""
        super().__init__(path)


@singleton
class DeleteRecycleDirectory(File):
    """Class to handle the delete recycle directory for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.TO_DELETE_RECYCLE_DIR.value) -> None:
        """Initialize the LogseqAnalyzerDeleteRecycleDir class."""
        super().__init__(path)


@singleton
class DeleteAssetsDirectory(File):
    """Class to handle the delete assets directory for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.TO_DELETE_ASSETS_DIR.value) -> None:
        """Initialize the LogseqAnalyzerDeleteAssetsDir class."""
        super().__init__(path)


@singleton
class CacheFile(File):
    """Class to handle the cache file for the Logseq Analyzer."""

    def __init__(self, path: str = Constants.CACHE_FILE.value) -> None:
        """Initialize the LogseqAnalyzerCacheFile class."""
        super().__init__(path)


@singleton
class BakDirectory(File):
    """Class to handle the bak directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerBakDir class."""
        super().__init__(path)


@singleton
class RecycleDirectory(File):
    """Class to handle the recycle directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerRecycleDir class."""
        super().__init__(path)


@singleton
class GlobalConfigFile(File):
    """Class to handle the global config file for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerGlobalConfigFile class."""
        super().__init__(path)


@singleton
class AssetsDirectory(File):
    """Class to handle the assets directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerAssetsDir class."""
        super().__init__(path)


@singleton
class DrawsDirectory(File):
    """Class to handle the draws directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerDrawsDir class."""
        super().__init__(path)


@singleton
class JournalsDirectory(File):
    """Class to handle the journals directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerJournalsDir class."""
        super().__init__(path)


@singleton
class PagesDirectory(File):
    """Class to handle the pages directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerPagesDir class."""
        super().__init__(path)


@singleton
class WhiteboardsDirectory(File):
    """Class to handle the whiteboards directory for the Logseq Analyzer."""

    def __init__(self, path: str = "") -> None:
        """Initialize the LogseqAnalyzerWhiteboardsDir class."""
        super().__init__(path)
