import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Set
from urllib.parse import unquote

import src.config as config


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
        elif root_path.name in target_dirs:
            for file in files:
                yield root_path / file
        else:
            logging.debug(f"Skipping directory {root_path} outside target directories")
            dirs.clear()


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
        target_dir = get_or_create_subdir(target_dir, target_subdir)

    for root, dirs, files in Path.walk(input_dir):
        for dir in dirs:
            try:
                shutil.move(Path(root) / dir, target_dir / dir)
                logging.warning(f"Moved folder: {dir}")
            except Exception as e:
                logging.error(f"Failed to move folder: {dir}: {e}")
        for file in files:
            try:
                shutil.move(Path(root) / file, target_dir / file)
                logging.warning(f"Moved file: {file}")
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
    to_delete_asset_subdir = get_or_create_subdir(to_delete_dir, config.DIR_ASSETS)

    for name in summary_is_asset_not_backlinked:
        file_path = Path(graph_meta_data[name]["file_path"])
        new_path = to_delete_asset_subdir / file_path.name
        try:
            shutil.move(file_path, new_path)
            logging.warning(f"Moved unlinked asset: {file_path} to {new_path}")
        except Exception as e:
            logging.error(f"Failed to move unlinked asset: {file_path} to {new_path}: {e}")


def merge_dicts(*dicts):
    """
    Merge multiple dictionaries into a single dictionary.

    Args:
        *dicts: Dictionaries to merge.
    Returns:
        dict: Merged dictionary.
    """
    result = {}
    for dict_data in dicts:
        for key, values in dict_data.items():
            if key not in result:
                result[key] = {}
            result[key].update(values)
    return result


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
        logging.warning(f"Subfolder does not exist: {target}")
        return None
    logging.debug(f"Successfully received: {target}")

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
        logging.warning(f"Parent folder does not exist: {parent}")
        return None
    elif not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created subdirectory: {target}")
        except Exception as e:
            logging.error(f"Failed to create subdirectory {target}: {e}")
            raise
    else:
        logging.debug(f"Subdirectory already exists: {target}")

    return target


def transform_date_format(cljs_format: str) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.

    Args:
        cljs_format (str): Clojure-style date format.

    Returns:
        str: Python-style date format.
    """

    def replace_token(match):
        token = match.group(0)
        return config.DATETIME_TOKEN_MAP.get(token, token)

    py_format = config.DATETIME_TOKEN_PATTERN.sub(replace_token, cljs_format)
    return py_format


def process_journal_key(key: str) -> str:
    """
    Process the journal key by converting it to a page title format.

    Args:
        key (str): The journal key (filename stem).

    Returns:
        str: Processed journal key as a page title.
    """
    py_file_name_format = transform_date_format(config.JOURNAL_FILE_NAME_FORMAT)
    py_page_title_format = transform_date_format(config.JOURNAL_PAGE_TITLE_FORMAT)

    try:
        date_object = datetime.strptime(key, py_file_name_format)
        page_title = date_object.strftime(py_page_title_format).lower()
        return page_title
    except ValueError:
        logging.warning(f"Could not parse journal key as date: {key}. Returning original key.")
        return key


def process_filename_key(key: str, parent: str) -> str:
    """
    Process the key name by removing the parent name and formatting it.

    For 'journals' parent, it formats the key as 'day-month-year dayOfWeek'.
    For other parents, it unquotes URL-encoded characters and replaces '___' with '/'.

    Args:
        key (str): The key name (filename stem).
        parent (str): The parent directory name.

    Returns:
        str: Processed key name.
    """
    if key.endswith(config.NAMESPACE_FILE_SEP):
        key = key.rstrip(config.NAMESPACE_FILE_SEP)

    if parent == config.DIR_JOURNALS:
        return process_journal_key(key)
    return unquote(key).replace(config.NAMESPACE_FILE_SEP, config.NAMESPACE_SEP).lower()
