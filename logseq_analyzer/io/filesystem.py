"""
File system operations for Logseq Analyzer.
"""

from math import sin
from pathlib import Path
import logging
import shutil

from ..config.analyzer_config import LogseqAnalyzerConfig

from ..utils.helpers import singleton


class File:
    """A class to represent a file in the Logseq Analyzer."""

    def __init__(self, path):
        """Initialize the File class with a path."""
        self.path = path

    # Getter for path property
    @property
    def path(self):
        """Get the path of the file."""
        return self._path

    # Setter for path property
    @path.setter
    def path(self, value):
        """Set the path of the file."""
        if isinstance(value, str):
            value = Path(value)
        self._path = value

    def validate(self):
        """Validate the file path."""
        if not self.path.exists():
            logging.error("File does not exist: %s", self.path)
            raise FileNotFoundError(f"File does not exist: {self.path}")
        logging.info("File exists: %s", self.path)

    def get_or_create_dir(self):
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

    def get_or_create_file(self):
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

    def initialize_dir(self):
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

    def initialize_file(self):
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

    def __init__(self):
        """Initialize the LogseqAnalyzerOutputDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["OUTPUT_DIR"])


@singleton
class LogFile(File):
    """Class to handle the log file for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerLogFile class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["LOG_FILE"])


@singleton
class GraphDirectory(File):
    """Class to handle the graph directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerGraphDir class."""
        super().__init__(LogseqAnalyzerConfig().config["ANALYZER"]["GRAPH_DIR"])


@singleton
class LogseqDirectory(File):
    """Class to handle the Logseq directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerLogseqDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["LOGSEQ_DIR"])


@singleton
class ConfigFile(File):
    """Class to handle the config file for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerConfigFile class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["CONFIG_FILE"])


@singleton
class DeleteDirectory(File):
    """Class to handle the delete directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerDeleteDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["TO_DELETE_DIR"])


@singleton
class DeleteBakDirectory(File):
    """Class to handle the delete bak directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerDeleteBakDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["TO_DELETE_BAK_DIR"])


@singleton
class DeleteRecycleDirectory(File):
    """Class to handle the delete recycle directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerDeleteRecycleDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["TO_DELETE_RECYCLE_DIR"])


@singleton
class DeleteAssetsDirectory(File):
    """Class to handle the delete assets directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerDeleteAssetsDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["TO_DELETE_ASSETS_DIR"])


@singleton
class CacheFile(File):
    """Class to handle the cache file for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerCacheFile class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["CACHE"])


@singleton
class BakDirectory(File):
    """Class to handle the bak directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerBakDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["BAK_DIR"])


@singleton
class RecycleDirectory(File):
    """Class to handle the recycle directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerRecycleDir class."""
        super().__init__(LogseqAnalyzerConfig().config["CONST"]["RECYCLE_DIR"])


@singleton
class GlobalConfigFile(File):
    """Class to handle the global config file for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerGlobalConfigFile class."""
        super().__init__(LogseqAnalyzerConfig().config["LOGSEQ_FILESYSTEM"]["GLOBAL_CONFIG_FILE"])


@singleton
class AssetsDirectory(File):
    """Class to handle the assets directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerAssetsDir class."""
        super().__init__(LogseqAnalyzerConfig().config["TARGET_DIRS"]["DIR_ASSETS"])


@singleton
class DrawsDirectory(File):
    """Class to handle the draws directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerDrawsDir class."""
        super().__init__(LogseqAnalyzerConfig().config["TARGET_DIRS"]["DIR_DRAWS"])


@singleton
class JournalsDirectory(File):
    """Class to handle the journals directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerJournalsDir class."""
        super().__init__(LogseqAnalyzerConfig().config["TARGET_DIRS"]["DIR_JOURNALS"])


@singleton
class PagesDirectory(File):
    """Class to handle the pages directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerPagesDir class."""
        super().__init__(LogseqAnalyzerConfig().config["TARGET_DIRS"]["DIR_PAGES"])


@singleton
class WhiteboardsDirectory(File):
    """Class to handle the whiteboards directory for the Logseq Analyzer."""

    def __init__(self):
        """Initialize the LogseqAnalyzerWhiteboardsDir class."""
        super().__init__(LogseqAnalyzerConfig().config["TARGET_DIRS"]["DIR_WHITEBOARDS"])
