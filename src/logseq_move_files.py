import argparse
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from src import config
from .helpers import get_or_create_subdir


def create_delete_directory() -> Path:
    """
    Create a directory for deleted files.

    Returns:
        Path: The path to the delete directory.
    """
    delete_dir = Path(config.DEFAULT_TO_DELETE_DIR)
    if not delete_dir.exists():
        logging.info(f"Creating directory: {delete_dir}")
        delete_dir.mkdir(parents=True, exist_ok=True)
    return delete_dir


def handle_move_files(
    args: argparse.Namespace, graph_meta_data: dict, assets: dict, bak: Path, recycle: Path, to_delete_dir: Path
) -> None:
    """
    Handle the moving of unlinked assets, bak, and recycle files to a specified directory.

    Args:
        args (argparse.Namespace): The command line arguments.
        graph_meta_data (dict): The graph metadata.
        assets (dict): The assets data.
        bak (Path): The path to the bak directory.
        recycle (Path): The path to the recycle directory.
        to_delete_dir (Path): The directory for deleted files.
    """
    moved_files = {}

    if args.move_unlinked_assets:
        moved_assets = move_unlinked_assets(assets, graph_meta_data, to_delete_dir)
        if moved_assets:
            moved_files["moved_assets"] = moved_assets

    if args.move_bak:
        moved_bak = move_all_folder_content(bak, to_delete_dir, config.DEFAULT_BAK_DIR)
        if moved_bak:
            moved_files["moved_bak"] = moved_bak

    if args.move_recycle:
        moved_recycle = move_all_folder_content(recycle, to_delete_dir, config.DEFAULT_RECYCLE_DIR)
        if moved_recycle:
            moved_files["moved_recycle"] = moved_recycle

    return moved_files


def move_all_folder_content(input_dir: Path, target_dir: Path, target_subdir: Optional[str] = "") -> List[str]:
    """
    Move all folders from one directory to another.

    Args:
        input_dir (Path): The source directory.
        target_dir (Path): The destination directory.
        target_subdir (Path): The subdirectory in the destination directory.

    Returns:
        List[str]: List of moved folder names.
    """
    folders = [input_dir, target_dir]
    for folder in folders:
        if not folder.exists():
            return

    if target_subdir:
        target_dir = get_or_create_subdir(target_dir, target_subdir)

    moved_content = []
    for root, dirs, files in Path.walk(input_dir):
        for directory in dirs:
            try:
                moved_content.append(directory)
                shutil.move(Path(root) / directory, target_dir / directory)
                logging.warning(f"Moved folder: {directory}")
            except Exception as e:
                logging.error(f"Failed to move folder: {directory}: {e}")
        for file in files:
            try:
                moved_content.append(file)
                shutil.move(Path(root) / file, target_dir / file)
                logging.warning(f"Moved file: {file}")
            except Exception as e:
                logging.error(f"Failed to move file: {file}: {e}")

    return moved_content


def move_unlinked_assets(
    summary_is_asset_not_backlinked: Dict[str, Any], graph_meta_data: Dict[str, Any], to_delete_dir: Path
) -> List[str]:
    """
    Move unlinked assets to a separate directory.

    Args:
        summary_is_asset_not_backlinked (Dict[str, Any]): Summary data for unlinked assets.
        graph_meta_data (Dict[str, Any]): Metadata for each file.
        to_delete_dir (Path): The directory to move unlinked assets to.

    Returns:
        List[str]: List of moved asset names.
    """
    to_delete_asset_subdir = get_or_create_subdir(to_delete_dir, config.DIR_ASSETS)

    moved_assets = []
    for name in summary_is_asset_not_backlinked:
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = to_delete_asset_subdir / file_path.name
        try:
            moved_assets.append(name)
            shutil.move(file_path, new_path)
            logging.warning(f"Moved unlinked asset: {file_path} to {new_path}")
        except Exception as e:
            logging.error(f"Failed to move unlinked asset: {file_path} to {new_path}: {e}")

    return moved_assets
