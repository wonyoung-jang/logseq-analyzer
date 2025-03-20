import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Set
from urllib.parse import unquote

from src import config


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
            logging.info(f"Skipping directory {root_path} outside target directories")
            dirs.clear()


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
        logging.info(f"Subdirectory already exists: {target}")

    return target


def convert_cljs_date_to_py(cljs_format: str) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.

    Args:
        cljs_format (str): Clojure-style date format.

    Returns:
        str: Python-style date format.
    """
    cljs_format = cljs_format.replace("o", "")

    def replace_token(match):
        token = match.group(0)
        return config.DATETIME_TOKEN_MAP.get(token, token)

    py_format = config.DATETIME_TOKEN_PATTERN.sub(replace_token, cljs_format)
    return py_format


def add_ordinal_suffix_to_day_of_month(day):
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return str(day) + suffix


def process_logseq_journal_key(key: str) -> str:
    """
    Process the journal key to create a page title.

    Args:
        key (str): The key name (filename stem).

    Returns:
        str: Processed page title.
    """
    py_file_name_format = convert_cljs_date_to_py(config.JOURNAL_FILE_NAME_FORMAT)
    py_page_title_no_ordinal = config.JOURNAL_PAGE_TITLE_FORMAT.replace("o", "")
    py_page_title_format_base = convert_cljs_date_to_py(py_page_title_no_ordinal)

    try:
        date_object = datetime.strptime(key, py_file_name_format)
        page_title_base = date_object.strftime(py_page_title_format_base).lower()
        if "o" in config.JOURNAL_PAGE_TITLE_FORMAT:
            day_number = date_object.day
            day_with_ordinal = add_ordinal_suffix_to_day_of_month(day_number)
            page_title = page_title_base.replace(f"{day_number}", day_with_ordinal)
        else:
            page_title = page_title_base
        page_title = page_title.replace("'", "")
        return page_title
    except ValueError as e:
        logging.warning(f"Failed to parse date from key '{key}', format `{py_file_name_format}`: {e}")
        return key


def process_logseq_filename_key(key: str, parent: str) -> str:
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
        return process_logseq_journal_key(key)
    return unquote(key).replace(config.NAMESPACE_FILE_SEP, config.NAMESPACE_SEP).lower()
