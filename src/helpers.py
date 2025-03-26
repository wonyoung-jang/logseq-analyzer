"""
Helper functions for file and date processing.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Generator, Set
from urllib.parse import unquote

from .config_loader import get_config


CONFIG = get_config()


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

        if root_path.name in target_dirs:
            for file in files:
                yield root_path / file
        else:
            logging.info("Skipping directory %s outside target directories", root_path)
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
        logging.warning("Subfolder does not exist: %s", target)
        return Path()

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
        logging.warning("Parent folder does not exist: %s", parent)
        return Path()

    if not target.exists():
        try:
            target.mkdir(parents=True, exist_ok=True)
            logging.info("Created subdirectory: %s", target)
        except PermissionError:
            logging.error("Permission denied to create subdirectory: %s", target)
        except OSError as e:
            logging.error("Error creating subdirectory: %s", e)
    else:
        logging.info("Subdirectory already exists: %s", target)

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
    datetime_token_map = CONFIG.get_datetime_token_map()
    datetime_token_pattern = CONFIG.get_datetime_token_pattern()

    def replace_token(match):
        token = match.group(0)
        return datetime_token_map.get(token, token)

    py_format = datetime_token_pattern.sub(replace_token, cljs_format)
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
    journal_page_format = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "JOURNAL_PAGE_TITLE_FORMAT")
    journal_file_format = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "JOURNAL_FILE_NAME_FORMAT")

    py_file_name_format = CONFIG.get("JOURNALS", "PY_FILE_FORMAT")
    if not py_file_name_format:
        py_file_name_format = convert_cljs_date_to_py(journal_file_format)
        CONFIG.set("JOURNALS", "PY_FILE_FORMAT", py_file_name_format)

    py_page_title_no_ordinal = journal_page_format.replace("o", "")

    py_page_title_format_base = CONFIG.get("JOURNALS", "PY_PAGE_BASE_FORMAT")
    if not py_page_title_format_base:
        py_page_title_format_base = convert_cljs_date_to_py(py_page_title_no_ordinal)
        CONFIG.set("JOURNALS", "PY_PAGE_BASE_FORMAT", py_page_title_format_base)

    try:
        date_object = datetime.strptime(key, py_file_name_format)
        page_title_base = date_object.strftime(py_page_title_format_base).lower()
        if "o" in journal_page_format:
            day_number = date_object.day
            day_with_ordinal = add_ordinal_suffix_to_day_of_month(day_number)
            page_title = page_title_base.replace(f"{day_number}", day_with_ordinal)
        else:
            page_title = page_title_base
        page_title = page_title.replace("'", "")
        return page_title
    except ValueError as e:
        logging.warning("Failed to parse date from key '%s', format `%s`: %s", key, py_file_name_format, e)
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
    ns_sep = CONFIG.get("LOGSEQ_NS", "NAMESPACE_SEP")
    ns_file_sep = CONFIG.get("LOGSEQ_NS", "NAMESPACE_FILE_SEP")
    dir_journals = CONFIG.get("LOGSEQ_CONFIG_DEFAULTS", "DIR_JOURNALS")

    if key.endswith(ns_file_sep):
        key = key.rstrip(ns_file_sep)

    if parent == dir_journals:
        return process_logseq_journal_key(key)

    return unquote(key).replace(ns_file_sep, ns_sep).lower()
