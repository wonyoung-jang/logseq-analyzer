"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile


def _move_src_to_dest(src: Path, dest: Path) -> None:
    """
    Move a file from source to destination.

    Args:
        src (Path): Source file path.
        dest (Path): Destination file path.
    """
    try:
        shutil.move(src, dest)
        logging.warning("Moved file: %s to %s", src, dest)
    except (shutil.Error, OSError) as e:
        logging.error("Failed to move file: %s to %s: %s", src, dest, e)


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
        unlinked_assets.insert(0, "=== Simulated only ===")
        return unlinked_assets

    for asset in unlinked_assets:
        src = asset.file_path
        dest = target_dir / src.name
        _move_src_to_dest(src, dest)

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
    moving_plan = []
    moved_names = []
    for root, dirs, files in Path.walk(source_dir):
        for directory in dirs:
            src = root / directory
            dest = target_dir / directory
            moving_plan.append((src, dest))
            moved_names.append(directory)
        for file in files:
            src = root / file
            dest = target_dir / file
            moving_plan.append((src, dest))
            moved_names.append(file)

    if not moving_plan:
        return []

    if not move:
        moved_names.insert(0, "=== Simulated only ===")
        return moved_names

    for src, dest in moving_plan:
        _move_src_to_dest(src, dest)

    return moved_names
