"""
Helper functions for file and date processing.
"""

import logging
from pathlib import Path
from typing import Generator, Set


def iter_files(directory: Path, target_dirs: Set[str]) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the given directory.

    If target_dirs is provided, only yield files that reside within directories
    whose names are in the target_dirs set.

    Args:
        directory (Path): The root directory to search.
        target_dirs (Set[str]): Set of allowed parent directory names.

    Yields:
        Path: File paths that match the criteria.
    """
    for root, dirs, files in Path.walk(directory):
        root_path = Path(root)
        if root_path == directory:
            continue

        if root_path.name in target_dirs:
            for file in files:
                yield root_path / file
        else:
            logging.info("Skipping directory %s outside target directories", root_path)
            dirs.clear()


def get_sub_file_or_folder(parent: Path, child: str) -> Path:
    """
    Get the path to a specific subfolder.

    Args:
        parent (Path): The path to the parent folder.
        child (str): The name of the target subfolder (e.g., "recycle", "bak", etc.).

    Returns:
        Path: The path to the specified subfolder or None if not found.
    """
    target = parent / child

    if not parent.exists() or not target.exists():
        logging.warning("Subfolder does not exist: %s", target)
        return Path()

    return target


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
        return Path()

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
