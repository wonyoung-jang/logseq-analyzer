"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Generator

from ..utils.enums import Moved

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile

logger = logging.getLogger(__name__)


def _move_src_to_dest(moving_plan: list[tuple[Path, Path]]) -> None:
    """
    Move a file from source to destination.

    Args:
        src (Path): Source file path.
        dest (Path): Destination file path.
    """
    try:
        for src, dest in moving_plan:
            shutil.move(src, dest)
            logger.warning("Moved file: %s to %s", src, dest)
    except (shutil.Error, OSError) as e:
        logger.error("Failed to move file: %s to %s: %s", src, dest, e)


def _yield_moved_assets(unlinked_assets: list["LogseqFile"], target_dir: Path) -> Generator[Path, None, None]:
    """
    Yield the paths of moved assets.

    Args:
        unlinked_assets (list[LogseqFile]): A list of unlinked assets.
        target_dir (Path): The directory to move assets to.

    Yields:
        Generator[Path, None, None]: A generator yielding the paths of moved assets.
    """
    for asset in unlinked_assets:
        src = asset.file_path
        dest = target_dir / src.name
        yield (src, dest)


def _yield_recycle_bak_dirs(source_dir: Path, target_dir: Path) -> Generator[Path, None, None]:
    """
    Yield the paths of recycle and bak directories.

    Args:
        source_dir (Path): The directory to search for recycle and bak directories.

    Yields:
        Generator[Path, None, None]: A generator yielding the paths of recycle and bak directories.
    """
    for root, dirs, files in Path.walk(source_dir):
        for name in dirs + files:
            src = root / name
            dest = target_dir / name
            yield (src, dest)


def handle_move_assets(move: bool, target_dir: Path, unlinked_assets: list["LogseqFile"]) -> list[str]:
    """
    Handle the moving of unlinked assets to a specified directory.

    Args:
        move (bool): If True, move the files. If False, simulate the move.
        target_dir (Path): The directory to delete assets to.
        unlinked_assets (list[LogseqFile]): A list of unlinked assets.

    Returns:
        list[str]: A list of names of the moved files/folders.
    """
    if not unlinked_assets:
        return []

    if not move:
        unlinked_assets.insert(0, Moved.SIMULATED_PREFIX.value)
        return unlinked_assets

    moving_plan = _yield_moved_assets(unlinked_assets, target_dir)
    _move_src_to_dest(moving_plan)

    return unlinked_assets


def handle_move_directory(move: bool, target_dir: Path, source_dir: Path) -> list[str]:
    """
    Move bak and recycle files to a specified directory.

    Args:
        move (bool): If True, move the files. If False, simulate the move.
        target_dir (Path): The directory to move files to.
        source_dir (Path): The directory to move files from.

    Returns:
        list[str]: A list of names of the moved files/folders.
    """
    moving_plan = list(_yield_recycle_bak_dirs(source_dir, target_dir))
    if not moving_plan:
        return []

    if not move:
        moving_plan.insert(0, Moved.SIMULATED_PREFIX.value)
        return moving_plan

    _move_src_to_dest(_yield_recycle_bak_dirs(source_dir, target_dir))

    return moving_plan
