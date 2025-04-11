"""
Config class for loading and managing configuration files.
"""

from pathlib import Path
from typing import Dict
import logging
import configparser
import re

from .helpers import get_file_or_folder
from .filesystem import File


class LogseqAnalyzerConfig:
    """
    A class to handle configuration file loading and management.
    """

    _instance = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LogseqAnalyzerConfig class."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            config_path = File("configuration/config.ini")
            config_path.validate()
            self.config = configparser.ConfigParser(
                allow_no_value=True,
                inline_comment_prefixes=("#", ";"),
                default_section="",
                interpolation=configparser.ExtendedInterpolation(),
                empty_lines_in_values=False,
                allow_unnamed_section=True,
            )
            self.config.optionxform = lambda option: option
            self.config.read(config_path.path)
            self.target_dirs = None
            self.built_in_properties = None
            self.datetime_token_map = None
            self.datetime_token_pattern = None

    def get(self, section, key, fallback=None):
        """Get a value from the config file"""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Set a value in the config file"""
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def get_section(self, section):
        """Get a section from the config file as a dictionary"""
        if section in self.config:
            return dict(self.config[section])
        return {}

    def get_built_in_properties(self):
        """Return the built-in properties as a frozenset"""
        properties_str = self.get("BUILT_IN_PROPERTIES", "PROPERTIES")
        self.built_in_properties = frozenset(properties_str.split(","))

    def get_datetime_token_map(self):
        """Return the datetime token mapping as a dictionary"""
        self.datetime_token_map = self.get_section("DATETIME_TOKEN_MAP")

    def get_datetime_token_pattern(self):
        """Return a compiled regex pattern for datetime tokens"""
        tokens = self.datetime_token_map.keys()
        pattern = "|".join(re.escape(k) for k in sorted(tokens, key=len, reverse=True))
        self.datetime_token_pattern = re.compile(pattern)

    def write(self, file):
        """Write the config to a file-like object"""
        self.config.write(file)

    def write_to_file(self):
        """Write the config to a file"""
        with open(f"{Path('configuration')}/user_config.ini", "w", encoding="utf-8") as config_file:
            self.write(config_file)

    def set_logseq_config_edn_data(self, ls_config: Dict[str, str]):
        """Set the Logseq configuration data."""
        self.set(
            "LOGSEQ_CONFIG",
            "JOURNAL_PAGE_TITLE_FORMAT",
            ls_config.get(":journal/page-title-format"),
        )
        self.set(
            "LOGSEQ_CONFIG",
            "JOURNAL_FILE_NAME_FORMAT",
            ls_config.get(":journal/file-name-format"),
        )
        self.set("LOGSEQ_CONFIG", "DIR_PAGES", ls_config.get(":pages-directory"))
        self.set("LOGSEQ_CONFIG", "DIR_JOURNALS", ls_config.get(":journals-directory"))
        self.set("LOGSEQ_CONFIG", "DIR_WHITEBOARDS", ls_config.get(":whiteboards-directory"))
        self.set("LOGSEQ_CONFIG", "NAMESPACE_FORMAT", ls_config.get(":file/name-format"))
        if self.get("LOGSEQ_CONFIG", "NAMESPACE_FORMAT") == ":triple-lowbar":
            self.set("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", "___")

    def get_logseq_target_dirs(self):
        """Get the target directories based on the configuration data."""
        self.target_dirs = set(self.get_section("TARGET_DIRS").values())
        # Validate target directories
        for dir_name in self.target_dirs:
            try:
                get_file_or_folder(Path(self.get("ANALYZER", "GRAPH_DIR")) / dir_name)
                logging.info("Target directory exists: %s", dir_name)
            except FileNotFoundError:
                logging.error("Target directory does not exist: %s", dir_name)

    def set_journal_py_formatting(self):
        """
        Set the formatting for journal files and pages in Python format.
        """
        journal_page_format = self.get("LOGSEQ_CONFIG", "JOURNAL_PAGE_TITLE_FORMAT")
        journal_file_format = self.get("LOGSEQ_CONFIG", "JOURNAL_FILE_NAME_FORMAT")
        if not self.get("LOGSEQ_JOURNALS", "PY_FILE_FORMAT"):
            py_file_name_format = self.convert_cljs_date_to_py(journal_file_format)
            self.set("LOGSEQ_JOURNALS", "PY_FILE_FORMAT", py_file_name_format)
        py_page_title_no_ordinal = journal_page_format.replace("o", "")
        if not self.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT"):
            py_page_title_format_base = self.convert_cljs_date_to_py(py_page_title_no_ordinal)
            self.set("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT", py_page_title_format_base)

    def convert_cljs_date_to_py(self, cljs_format) -> str:
        """
        Convert a Clojure-style date format to a Python-style date format.
        """
        cljs_format = cljs_format.replace("o", "")
        return self.datetime_token_pattern.sub(self.replace_token, cljs_format)

    def replace_token(self, match):
        """
        Replace a date token with its corresponding Python format.
        """
        token = match.group(0)
        return self.datetime_token_map.get(token, token)
