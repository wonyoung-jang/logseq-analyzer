"""
Config class for loading and managing configuration files.
"""

from pathlib import Path
import configparser
import re


class LogseqAnalyzerConfig:
    """
    A class to handle configuration file loading and management.
    """

    def __init__(self):
        """Initialize the LogseqAnalyzerConfig class."""
        self.config_path = Path("configuration") / "config.ini"
        self.config = configparser.ConfigParser(
            allow_no_value=True,
            inline_comment_prefixes=("#", ";"),
            default_section="None",
            interpolation=configparser.ExtendedInterpolation(),
        )
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        self.config.optionxform = lambda option: option
        self.config.read(self.config_path)
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

    def get_datetime_token_map(self):
        """Return the datetime token mapping as a dictionary"""
        self.datetime_token_map = self.get_section("DATETIME_TOKEN_MAP")

    def get_datetime_token_pattern(self):
        """Return a compiled regex pattern for datetime tokens"""
        tokens = self.datetime_token_map.keys()
        pattern = "|".join(re.escape(k) for k in sorted(tokens, key=len, reverse=True))
        self.datetime_token_pattern = re.compile(pattern)

    def get_built_in_properties(self):
        """Return the built-in properties as a frozenset"""
        properties_str = self.get("BUILT_IN_PROPERTIES", "PROPERTIES")
        self.built_in_properties = frozenset(properties_str.split(","))

    def write(self, file):
        """Write the config to a file-like object"""
        self.config.write(file)

    def get_logseq_target_dirs(self):
        """Get the target directories based on the configuration data."""
        self.target_dirs = set(self.get_section("TARGET_DIRS").values())

    def set_logseq_config_edn_data(self, config_edn_data: dict) -> None:
        """Set the Logseq configuration data."""
        self.set("LOGSEQ_CONFIG", "JOURNAL_PAGE_TITLE_FORMAT", config_edn_data["journal_page_title_format"])
        self.set("LOGSEQ_CONFIG", "JOURNAL_FILE_NAME_FORMAT", config_edn_data["journal_file_name_format"])
        self.set("LOGSEQ_CONFIG", "DIR_PAGES", config_edn_data["pages_directory"])
        self.set("LOGSEQ_CONFIG", "DIR_JOURNALS", config_edn_data["journals_directory"])
        self.set("LOGSEQ_CONFIG", "DIR_WHITEBOARDS", config_edn_data["whiteboards_directory"])
        self.set("LOGSEQ_CONFIG", "NAMESPACE_FORMAT", config_edn_data["file_name_format"])
        ns_fmt = self.get("LOGSEQ_CONFIG", "NAMESPACE_FORMAT")
        if ns_fmt == ":triple-lowbar":
            self.set("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", "___")
