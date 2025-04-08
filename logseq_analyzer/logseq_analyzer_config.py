"""
Config class for loading and managing configuration files.
"""

from pathlib import Path
import logging
import configparser
import re

from .helpers import get_file_or_folder


class LogseqAnalyzerConfig:
    """
    A class to handle configuration file loading and management.
    """

    def __init__(self):
        """Initialize the LogseqAnalyzerConfig class."""
        config_path = Path("configuration") / "config.ini"
        self.config = configparser.ConfigParser(
            allow_no_value=True,
            inline_comment_prefixes=("#", ";"),
            default_section="",
            interpolation=configparser.ExtendedInterpolation(),
            empty_lines_in_values=False,
            allow_unnamed_section=True,
        )
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        self.config.optionxform = lambda option: option
        self.config.read(config_path)
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

    def set_logseq_config_edn_data(self, gc, report_format: str):
        """Set the Logseq configuration data."""
        self.set("ANALYZER", "REPORT_FORMAT", report_format)
        self.set("CONST", "GRAPH_DIR", gc.directory)
        self.set(
            "LOGSEQ_CONFIG",
            "JOURNAL_PAGE_TITLE_FORMAT",
            gc.ls_config.get(":journal/page-title-format"),
        )
        self.set(
            "LOGSEQ_CONFIG",
            "JOURNAL_FILE_NAME_FORMAT",
            gc.ls_config.get(":journal/file-name-format"),
        )
        self.set("LOGSEQ_CONFIG", "DIR_PAGES", gc.ls_config.get(":pages-directory"))
        self.set("LOGSEQ_CONFIG", "DIR_JOURNALS", gc.ls_config.get(":journals-directory"))
        self.set("LOGSEQ_CONFIG", "DIR_WHITEBOARDS", gc.ls_config.get(":whiteboards-directory"))
        self.set("LOGSEQ_CONFIG", "NAMESPACE_FORMAT", gc.ls_config.get(":file/name-format"))
        if self.get("LOGSEQ_CONFIG", "NAMESPACE_FORMAT") == ":triple-lowbar":
            self.set("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", "___")

    def get_logseq_target_dirs(self):
        """Get the target directories based on the configuration data."""
        self.target_dirs = set(self.get_section("TARGET_DIRS").values())
        # Validate target directories
        for dir_name in self.target_dirs:
            try:
                get_file_or_folder(Path(self.get("CONST", "GRAPH_DIR")) / dir_name)
                logging.info("Target directory exists: %s", dir_name)
            except FileNotFoundError:
                logging.error("Target directory does not exist: %s", dir_name)
