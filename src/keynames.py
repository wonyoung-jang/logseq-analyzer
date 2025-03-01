import logging
import re
import src.config as config
from datetime import datetime
from urllib.parse import unquote


def transform_date_format(cljs_format: str) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.

    Args:
        cljs_format (str): Clojure-style date format.

    Returns:
        str: Python-style date format.
    """
    token_map = config.DATETIME_TOKEN_MAP
    token_pattern = re.compile("|".join(re.escape(k) for k in sorted(token_map, key=len, reverse=True)))

    def replace_token(match):
        token = match.group(0)
        return token_map.get(token, token)

    py_format = token_pattern.sub(replace_token, cljs_format)
    return py_format


def process_journal_key(key: str) -> str:
    """
    Process the journal key by converting it to a page title format.

    Args:
        key (str): The journal key (filename stem).

    Returns:
        str: Processed journal key as a page title.
    """
    page_title_format = config.JOURNAL_PAGE_TITLE_FORMAT
    file_name_format = config.JOURNAL_FILE_NAME_FORMAT
    py_file_name_format = transform_date_format(file_name_format)
    py_page_title_format = transform_date_format(page_title_format)

    try:
        date_object = datetime.strptime(key, py_file_name_format)
        page_title = date_object.strftime(py_page_title_format).lower()
        return page_title
    except ValueError:
        logging.warning(f"Could not parse journal key as date: {key}. Returning original key.")
        return key


def process_key_name(key: str, parent: str) -> str:
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

    if parent == config.JOURNALS:
        return process_journal_key(key)
    return unquote(key).replace(config.NAMESPACE_FILE_SEP, config.NAMESPACE_SEP).lower()
