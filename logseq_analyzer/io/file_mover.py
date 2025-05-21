"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path

from ..logseq_file.file import LogseqFile


def handle_move_assets(move: bool, target_dir: Path, unlinked_assets: list[LogseqFile]) -> list[str]:
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
        prefix = "=== Simulated only ==="
        unlinked_assets.insert(0, prefix)
        return unlinked_assets

    for asset in unlinked_assets:
        src = asset.file_path
        dest = target_dir / src.name
        try:
            shutil.move(src, dest)
            logging.warning("Moved unlinked asset: %s to %s", src, dest)
        except (shutil.Error, OSError) as e:
            logging.error("Failed to move unlinked asset: %s to %s: %s", src, dest, e)

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
        for dir in dirs:
            src = root / dir
            dest = target_dir / dir
            moving_plan.append((src, dest))
            moved_names.append(dir)
        for file in files:
            src = root / file
            dest = target_dir / file
            moving_plan.append((src, dest))
            moved_names.append(file)

    if not moving_plan:
        return []

    if not move:
        prefix = "=== Simulated only ==="
        moved_names.insert(0, prefix)
        return moved_names

    for src, dest in moving_plan:
        try:
            shutil.move(src, dest)
            logging.warning("Moved folder: %s to %s", src, dest)
        except (shutil.Error, OSError) as e:
            logging.error("Failed to move folder: %s to %s: %s", src, dest, e)

    return moved_names
