"""File system operations for Logseq Analyzer."""

import logging
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def check_must_exist(path: Path, *, is_dir: bool = False) -> None:
    """Validate the file path."""
    if not path.exists():
        logger.error("File does not exist: %s", path)
        msg = f"File does not exist: {path}"
        raise FileNotFoundError(msg)
    if is_dir and not path.is_dir():
        logger.error("Path is not a directory: %s", path)
        msg = f"Path is not a directory: {path}"
        raise NotADirectoryError(msg)
    if not is_dir and not path.is_file():
        logger.error("Path is not a file: %s", path)
        msg = f"Path is not a file: {path}"
        raise FileNotFoundError(msg)
    logger.info("%s exists", path)


def clean(path: Path, *, is_dir: bool = False) -> None:
    """Clean up the file or directory."""
    try:
        if is_dir:
            shutil.rmtree(path)
            logger.info("Deleted directory: %s", path)
        else:
            path.unlink()
            logger.info("Deleted file: %s", path)
    except OSError:
        logger.exception("Error deleting path")
        raise


def make_if_missing(path: Path, *, is_dir: bool = False) -> None:
    """Create the file or directory if it does not exist."""
    try:
        if not path.exists():
            if is_dir:
                path.mkdir(parents=True, exist_ok=True)
                logger.info("Created directory: %s", path)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch(exist_ok=True)
                logger.info("Created file: %s", path)
    except OSError:
        logger.exception("Error creating path")
        raise


def check_path(
    path: Path,
    *,
    is_dir: bool = False,
    must_exist: bool = False,
    clean_on_init: bool = False,
    create: bool = True,
) -> None:
    """Check and prepare the file or directory path."""
    if must_exist:
        check_must_exist(path, is_dir=is_dir)
    if clean_on_init and path.exists():
        clean(path, is_dir=is_dir)
    if create:
        make_if_missing(path, is_dir=is_dir)
    logger.info("Checked path: %s", path)
