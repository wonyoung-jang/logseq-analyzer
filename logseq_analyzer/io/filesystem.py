"""
File system operations for Logseq Analyzer.
"""

from pathlib import Path
import logging
import shutil


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

    @path.deleter
    def path(self):
        """Delete the path of the file."""
        del self._path

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
