"""
Helper functions for file and date processing.
"""

from pathlib import Path
from typing import Generator, Set, List, Pattern
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


def get_or_create_file_or_dir(path: Path) -> Path:
    """
    Get a path or create it if it doesn't exist.

    Args:
        path (Path): The path to the target file or folder.

    Returns:
        Path: The path to the specified file or folder.
    """
    try:
        path.resolve(strict=True)
        return path
    except FileNotFoundError:
        logging.info("Creating path: %s", path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            logging.info("Created path: %s", path)
            return path
        except PermissionError:
            logging.error("Permission denied to create path: %s", path)
            return None
        except OSError as e:
            logging.error("Error creating path: %s", e)
            return None


def find_all_lower(pattern: Pattern, text: str) -> List[str]:
    """Find all matches of a regex pattern in the text, returning them in lowercase."""
    return [match.lower() for match in pattern.findall(text)]


def process_aliases(aliases: str) -> List[str]:
    """Process aliases to extract individual aliases."""
    aliases = aliases.strip()
    results = []
    current = []
    inside_brackets = False
    i = 0
    while i < len(aliases):
        if aliases[i : i + 2] == "[[":
            inside_brackets = True
            i += 2
        elif aliases[i : i + 2] == "]]":
            inside_brackets = False
            i += 2
        elif aliases[i] == "," and not inside_brackets:
            part = "".join(current).strip().lower()
            if part:
                results.append(part)
            current = []
            i += 1
        else:
            current.append(aliases[i])
            i += 1

    part = "".join(current).strip().lower()
    if part:
        results.append(part)
    return results
