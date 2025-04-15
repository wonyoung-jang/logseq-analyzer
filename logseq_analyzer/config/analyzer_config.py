"""
Config class for loading and managing configuration files.
"""

from pathlib import Path
from typing import Dict
import configparser

from ..io.filesystem import File
from ..utils.enums import Core


def lambda_optionxform(option: str) -> str:
    """
    Custom optionxform function to preserve case sensitivity of options.
    """
    return option


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
            self.config.optionxform = lambda_optionxform
            self.config.read(config_path.path)
            self.target_dirs = None

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

    def write(self, file):
        """Write the config to a file-like object"""
        self.config.write(file)

    def write_to_file(self):
        """Write the config to a file"""
        with open(f"{Path('configuration')}/user_config.ini", "w", encoding="utf-8") as config_file:
            self.write(config_file)

    def set_logseq_config_edn_data(self, ls_config: Dict[str, str]):
        """Set the Logseq configuration data."""
        self.set("LOGSEQ_CONFIG", "DIR_PAGES", ls_config.get(":pages-directory", "pages"))
        self.set("LOGSEQ_CONFIG", "DIR_JOURNALS", ls_config.get(":journals-directory", "journals"))
        self.set("LOGSEQ_CONFIG", "DIR_WHITEBOARDS", ls_config.get(":whiteboards-directory", "whiteboards"))

        ns_format = ls_config.get(":file/name-format")
        self.set("LOGSEQ_CONFIG", "NAMESPACE_FORMAT", ns_format)
        if ns_format == ":triple-lowbar":
            self.set("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", Core.NS_FILE_SEP_TRIPLE_LOWBAR.value)

    def get_logseq_target_dirs(self):
        """Get the target directories based on the configuration data."""
        self.target_dirs = {
            self.config["LOGSEQ_CONFIG"]["DIR_ASSETS"],
            self.config["LOGSEQ_CONFIG"]["DIR_DRAWS"],
            self.config["LOGSEQ_CONFIG"]["DIR_PAGES"],
            self.config["LOGSEQ_CONFIG"]["DIR_JOURNALS"],
            self.config["LOGSEQ_CONFIG"]["DIR_WHITEBOARDS"],
        }
