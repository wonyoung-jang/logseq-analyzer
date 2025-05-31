"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Generator

from ..utils.enums import MovedFiles

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile

logger = logging.getLogger(__name__)

__all__ = [
    "yield_asset_paths",
    "yield_bak_rec_paths",
    "process_moves",
]


def yield_asset_paths(unlinked_assets: set["LogseqFile"]) -> Generator[Path, None, None]:
    """Yield the file paths of unlinked assets."""
    for asset in unlinked_assets:
        yield asset.path


def yield_bak_rec_paths(source_dir: Path) -> Generator[Path, None, None]:
    """Yield the file paths of bak and recycle directories."""
    for root, dirs, files in Path.walk(source_dir):
        for name in dirs + files:
            yield root / name


def process_moves(move: bool, target_dir: Path, paths: list[Path]) -> list[str]:
    """
    Process the moving of files to a specified directory.

    Args:
        move (bool): If True, move the files. If False, simulate the move.
        target_dir (Path): The directory to move files to.
        paths (list[Path]): A list of file paths to move.

    Returns:
        list[str]: A list of names of the moved files/folders.
    """
    names = [path.name for path in paths]
    if not names:
        return []

    if not move:
        return [MovedFiles.SIMULATED_PREFIX.value] + names

    for src in paths:
        dest = target_dir / src.name
        try:
            shutil.move(str(src), str(dest))
            logger.warning("Moved file: %s to %s", src, dest)
        except (shutil.Error, OSError) as e:
            logger.error("Failed to move file: %s to %s: %s", src, dest, e)
    return names
