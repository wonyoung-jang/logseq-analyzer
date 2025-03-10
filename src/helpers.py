import logging
import shutil
import src.config as config
from pathlib import Path
from typing import Optional, Dict, Any, Generator, List


def iter_files(directory: Path, target_dirs: Optional[List[str]] = None) -> Generator[Path, None, None]:
    """
    Recursively iterate over files in the given directory.

    If target_dirs is provided, only yield files that reside within directories
    whose names are in the target_dirs list.

    Args:
        directory (Path): The root directory to search.
        target_dirs (Optional[List[str]]): List of allowed parent directory names.

    Yields:
        Path: File paths that match the criteria.
    """
    if not directory.exists() or not directory.is_dir():
        logging.error(f"Directory not found: {directory}")
        return

    for path in directory.rglob("*"):
        if path.is_file():
            if target_dirs:
                if path.parent.name in target_dirs:
                    yield path
                else:
                    logging.info(f"Skipping file {path} outside target directories")
            else:
                yield path


def move_all_folder_content(input_dir: Path, target_dir: Path, target_subdir: Optional[Path] = None) -> None:
    """
    Move all folders from one directory to another.

    Args:
        input_dir (Path): The source directory.
        target_dir (Path): The destination directory.
        target_subdir (Path): The subdirectory in the destination directory.
    """
    folders = [input_dir, target_dir]
    for folder in folders:
        if not folder.exists():
            return

    if target_subdir:
        target_dir = target_dir / target_subdir
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created target subdirectory: {target_dir}")

    for root, dirs, files in Path.walk(input_dir):
        for dir in dirs:
            try:
                shutil.move(Path(root) / dir, target_dir / dir)
                logging.info(f"Moved folder: {dir}")
            except Exception as e:
                logging.error(f"Failed to move folder: {dir}: {e}")
        for file in files:
            try:
                shutil.move(Path(root) / file, target_dir / file)
                logging.info(f"Moved file: {file}")
            except Exception as e:
                logging.error(f"Failed to move file: {file}: {e}")


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
    to_delete_asset_subdir = to_delete_dir / config.DIR_ASSETS
    if not to_delete_asset_subdir.exists():
        to_delete_asset_subdir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created unlinked assets directory: {to_delete_asset_subdir}")

    for name in summary_is_asset_not_backlinked.keys():
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = to_delete_asset_subdir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.info(f"Moved unlinked asset: {file_path} to {new_path}")
        except Exception as e:
            logging.error(f"Failed to move unlinked asset: {file_path} to {new_path}: {e}")
