"""
LogseqFile class to represent a Logseq file.
This class contains metadata about the file, including its name, path, creation date, modification date, and content.
"""

from datetime import datetime
import logging
from pathlib import Path
from pprint import pprint
from urllib.parse import unquote

import src.config as config
from src.compile_regex import compile_re_content

PATTERNS = compile_re_content()


class LogseqFile:
    def __init__(self, file_path: Path):
        stat = file_path.stat()
        parent = file_path.parent.name
        name = self.process_filename_key(file_path.stem, parent)
        suffix = file_path.suffix.lower() if file_path.suffix else None
        now = datetime.now().replace(microsecond=0)

        try:
            date_created = datetime.fromtimestamp(stat.st_birthtime).replace(microsecond=0)
        except AttributeError:
            date_created = datetime.fromtimestamp(stat.st_ctime).replace(microsecond=0)
            logging.warning(f"File creation time (st_birthtime) not available for {file_path}. Using st_ctime instead.")

        date_modified = datetime.fromtimestamp(stat.st_mtime).replace(microsecond=0)

        time_existed = now - date_created
        time_unmodified = now - date_modified

        self.id = name[:2].lower() if len(name) > 1 else f"!{name[0].lower()}"
        self.name = name
        self.name_secondary = f"{name} {parent} + {suffix}".lower()
        self.file_path = str(file_path)
        self.file_path_parent_name = parent.lower()
        self.file_path_name = name.lower()
        self.file_path_suffix = suffix.lower() if suffix else None
        self.file_path_parts = file_path.parts
        self.date_created = date_created
        self.date_modified = date_modified
        self.time_existed = time_existed
        self.time_unmodified = time_unmodified
        self.size = stat.st_size
        self.uri = file_path.as_uri()

        content = None
        try:
            content = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.warning(f"File not found: {file_path}")
        except Exception as e:
            logging.warning(f"Failed to read file {file_path}: {e}")

        self.char_count = 0
        self.bullet_count = 0
        self.bullet_density = 0
        if content:
            self.char_count = len(content)
            bullet_count = len(PATTERNS["bullet"].findall(content))
            self.bullet_count = bullet_count
            self.bullet_density = self.char_count // bullet_count if bullet_count > 0 else 0

    def transform_date_format(self, cljs_format: str) -> str:
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

    def process_journal_key(self, key: str) -> str:
        """
        Process the journal key by converting it to a page title format.

        Args:
            key (str): The journal key (filename stem).

        Returns:
            str: Processed journal key as a page title.
        """
        page_title_format = config.JOURNAL_PAGE_TITLE_FORMAT
        file_name_format = config.JOURNAL_FILE_NAME_FORMAT
        py_file_name_format = self.transform_date_format(file_name_format)
        py_page_title_format = self.transform_date_format(page_title_format)

        try:
            date_object = datetime.strptime(key, py_file_name_format)
            page_title = date_object.strftime(py_page_title_format).lower()
            return page_title
        except ValueError:
            logging.warning(f"Could not parse journal key as date: {key}. Returning original key.")
            return key

    def process_filename_key(self, key: str, parent: str) -> str:
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
        if parent == config.DIR_JOURNALS:
            return self.process_journal_key(key)

        if key.endswith(config.NAMESPACE_FILE_SEP):
            key = key.rstrip(config.NAMESPACE_FILE_SEP)

        return unquote(key).replace(config.NAMESPACE_FILE_SEP, config.NAMESPACE_SEP).lower()
