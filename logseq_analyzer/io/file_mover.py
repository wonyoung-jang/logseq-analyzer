"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path

from ..logseq_file.file import LogseqFile


def handle_move_assets(argument: bool, delete_assets_dir: Path, not_backlinked: list[LogseqFile]) -> list[str]:
    """
    Handle the moving of unlinked assets, bak, and recycle files to a specified directory.

    Args:
        argument (bool): If True, move the files. If False, simulate the move.
        delete_assets_dir (Path): The directory to delete assets to.
        not_backlinked (list[LogseqFile]): A list of unlinked assets.

    Returns:
        list[str]: A list of names of the moved files/folders.
    """
    if not_backlinked:
        if argument:
            _move_unlinked_assets(not_backlinked, delete_assets_dir)
            return not_backlinked
        not_backlinked.insert(0, "=== Simulated only ===")
        return not_backlinked
    return []


def _move_unlinked_assets(not_backlinked: list[LogseqFile], delete_assets_dir: Path) -> None:
    """
    Move unlinked assets to a separate directory.

    Args:
        not_backlinked (list[LogseqFile]): A list of unlinked asset file paths.
        delete_assets_dir (Path): The directory to move unlinked assets to.
    """
    for asset in not_backlinked:
        file_path = asset.file_path
        new_path = delete_assets_dir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.warning("Moved unlinked asset: %s to %s", file_path, new_path)
        except (shutil.Error, OSError) as e:
            logging.error("Failed to move unlinked asset: %s to %s: %s", file_path, new_path, e)


def handle_move_directory(argument: bool, output_dir: Path, logseq_dir: Path) -> list[str]:
    """
    Move bak and recycle files to a specified directory.

    Args:
        argument (bool): If True, move the files. If False, simulate the move.
        output_dir (Path): The directory to move files to.
        logseq_dir (Path): The directory to move files from.

    Returns:
        list[str]: A list of names of the moved files/folders.
    """
    moved, moved_names = _get_all_folder_content(output_dir, logseq_dir)

    if not moved:
        return []

    if not argument:
        moved_names.insert(0, "=== Simulated only ===")
        return moved_names

    _move_all_folder_content(moved)
    return moved_names


def _get_all_folder_content(output_dir: Path, logseq_dir: Path) -> tuple[list[tuple], list[str]]:
    """
    Move all folders from one directory to another.

    Args:
        output_dir (Path): The directory to move files to.
        logseq_dir (Path): The directory to move files from.

    Returns:
        tuple[list[tuple], list[str]]: A tuple containing a list of tuples with source and destination paths,
                                        and a list of names of the moved files/folders.
    """
    moved_content = []
    moved_content_names = []
    for root, dirs, files in Path.walk(logseq_dir):
        for directory in dirs:
            current_dir_path = root / directory
            moved_dir_path = output_dir / directory
            moved_content.append((current_dir_path, moved_dir_path))
            moved_content_names.append(directory)
        for file in files:
            current_file_path = root / file
            moved_file_path = output_dir / file
            moved_content.append((current_file_path, moved_file_path))
            moved_content_names.append(file)
    return moved_content, moved_content_names


def _move_all_folder_content(moved_content: list[tuple]) -> None:
    """
    Move all folders from one directory to another.

    Args:
        moved_content (list[Tuple]): list of tuples containing source and destination paths.
    """
    for old_path, new_path in moved_content:
        try:
            shutil.move(old_path, new_path)
            logging.warning("Moved folder: %s to %s", old_path, new_path)
        except (shutil.Error, OSError) as e:
            logging.error("Failed to move folder: %s to %s: %s", old_path, new_path, e)
