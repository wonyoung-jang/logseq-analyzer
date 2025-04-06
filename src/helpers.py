"""
Helper functions for file and date processing.
"""

from pathlib import Path
from typing import Generator, Set
import logging


class FileSystem:
    """
    A simple class to encapsulate file system operations for easier mocking/testing.
    """

    def __init__(self, root_dir: Path, target_dirs: Set[str]):
        """
        Initialize the FileSystem class.
        """
        self.root_dir = root_dir
        self.target_dirs = target_dirs

    def iter_files(self) -> Generator[Path, None, None]:
        """
        Recursively iterate over files in the root directory.
        """
        for root, dirs, files in Path.walk(self.root_dir):
            path_root = Path(root)
            if path_root == self.root_dir:
                continue

            if path_root.name in self.target_dirs:
                for file in files:
                    yield path_root / file
            else:
                logging.info("Skipping directory %s outside target directories", path_root)
                dirs.clear()


def get_file_or_folder(path: Path) -> Path:
    """
    Get the path to an existing path.

    Args:
        path (Path): The path

    Returns:
        Path: The path to the specified path or None if not found.
    """
    if isinstance(path, str):
        path = Path(path)

    try:
        path.resolve(strict=True)
        return path
    except FileNotFoundError:
        logging.warning("Path does not exist: %s", path)
        return None


def get_or_create_subdir(parent: Path, child: str) -> Path:
    """
    Get a subdirectory or create it if it doesn't exist.

    Args:
        parent (Path): The path to the parent folder.
        child (str): The name of the target subfolder.

    Returns:
        Path: The path to the specified subfolder.
    """
    target = parent / child

    if not parent.exists():
        logging.warning("Parent folder does not exist: %s", parent)

    if not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            logging.info("Created subdirectory: %s", target)
        except PermissionError:
            logging.error("Permission denied to create subdirectory: %s", target)
        except OSError as e:
            logging.error("Error creating subdirectory: %s", e)
    else:
        logging.info("Subdirectory already exists: %s", target)

    return target


def path_validator(path: str) -> bool:
    """
    Validate if a given path exists.

    Args:
        path (str): The path to validate.

    Returns:
        bool: True if the path exists, False otherwise.
    """
    try:
        Path(path).resolve(strict=True)
        return True
    except FileNotFoundError:
        logging.warning("Path does not exist: %s", path)
        return False
