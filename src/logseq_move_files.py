"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .helpers import get_or_create_subdir
from .config_loader import get_config


CONFIG = get_config()


def create_delete_directory() -> Path:
    """
    Create a directory for deleted files.

    Returns:
        Path: The path to the delete directory.
    """
    delete_dir = Path(CONFIG.get("ANALYZER", "TO_DELETE_DIR"))
    if not delete_dir.exists():
        logging.info("Creating directory: %s", delete_dir)
        delete_dir.mkdir(parents=True, exist_ok=True)
    return delete_dir


def handle_move_files(
    argument: bool,
    graph_data: dict,
    unlinked_assets: dict,
    to_delete_dir: Path,
) -> List[str]:
    """
    Handle the moving of unlinked assets, bak, and recycle files to a specified directory.

    Args:
        argument: The command line arguments.
        graph_data (dict): The graph data.
        unlinked_assets (dict): The assets data.
        to_delete_dir (Path): The directory for deleted files.

    Returns:
        List[str]: A list of moved files or None.
    """
    if unlinked_assets:
        if argument:
            move_unlinked_assets(unlinked_assets, graph_data, to_delete_dir)
            return unlinked_assets
        unlinked_assets = ["=== Simulated only ==="] + unlinked_assets
        return unlinked_assets

    return []


def handle_move_directory(argument: bool, target_dir: Path, to_delete_dir: Path, default_dir: Path) -> List[str]:
    """
    Move bak and recycle files to a specified directory.

    Args:
        argument (bool): The command line argument for moving files.
        target_dir (Path): The directory to move files from.
        to_delete_dir (Path): The directory to move files to.
        default_dir (Path): The default directory for bak and recycle files.

    Returns:
        List[str]: A list of moved files or an empty list if no files were moved.
    """
    moved, moved_names = get_all_folder_content(target_dir, to_delete_dir, default_dir)

    if moved:
        if argument:
            move_all_folder_content(moved)
            return moved_names
        moved_names = ["=== Simulated only ==="] + moved_names
        return moved_names

    return []


def get_all_folder_content(
    input_dir: Path, target_dir: Path, target_subdir: Optional[str] = ""
) -> Tuple[List[Tuple[Path, Path]], List[str]]:
    """
    Move all folders from one directory to another.

    Args:
        input_dir (Path): The source directory.
        target_dir (Path): The destination directory.
        target_subdir (Path): The subdirectory in the destination directory.

    Returns:
        Tuple[List[Tuple[Path, Path]], List[str]]: A tuple containing:
            - List of tuples with source and destination paths.
            - List of names of moved files and folders.
    """
    for folder in [input_dir, target_dir]:
        if not folder.exists():
            return [], []

    if target_subdir:
        target_dir = get_or_create_subdir(target_dir, target_subdir)

    moved_content = []
    moved_content_names = []

    for root, dirs, files in Path.walk(input_dir):
        for directory in dirs:
            current_dir_path = Path(root) / directory
            moved_dir_path = target_dir / directory
            moved_content.append((current_dir_path, moved_dir_path))
            moved_content_names.append(directory)
        for file in files:
            current_file_path = Path(root) / file
            moved_file_path = target_dir / file
            moved_content.append((current_file_path, moved_file_path))
            moved_content_names.append(file)

    return moved_content, moved_content_names


def move_all_folder_content(moved_content: List[Tuple]) -> None:
    """
    Move all folders from one directory to another.

    Args:
        moved_content (List[Tuple]): List of tuples containing source and destination paths.
    """
    for old_path, new_path in moved_content:
        try:
            shutil.move(old_path, new_path)
            logging.warning("Moved folder: %s to %s", old_path, new_path)
        except (shutil.Error, OSError) as e:
            logging.error("Failed to move folder: %s to %s: %s", old_path, new_path, e)


def move_unlinked_assets(
    summary_is_asset_not_backlinked: Dict[str, Any], graph_meta_data: Dict[str, Any], to_delete_dir: Path
) -> None:
    """
    Move unlinked assets to a separate directory.

    Args:
        summary_is_asset_not_backlinked (Dict[str, Any]): Summary data for unlinked assets.
        graph_meta_data (Dict[str, Any]): Metadata for each file.
        to_delete_dir (Path): The directory to move unlinked assets to.
    """
    asset_dir = CONFIG.get("LOGSEQ_CONFIG", "DIR_ASSETS")
    to_delete_asset_subdir = get_or_create_subdir(to_delete_dir, asset_dir)

    for name in summary_is_asset_not_backlinked:
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = to_delete_asset_subdir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.warning("Moved unlinked asset: %s to %s", file_path, new_path)
        except (shutil.Error, OSError) as e:
            logging.error("Failed to move unlinked asset: %s to %s: %s", file_path, new_path, e)
