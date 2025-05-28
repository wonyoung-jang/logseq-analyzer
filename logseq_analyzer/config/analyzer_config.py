"""
Config class for loading and managing configuration files.
"""

import configparser
from pathlib import Path

from ..utils.enums import Config, Output
from ..utils.helpers import singleton


def lambda_optionxform(option: str) -> str:
    """
    Custom optionxform function to preserve case sensitivity of options.
    """
    return option


@singleton
class LogseqAnalyzerConfig:
    """A class to handle configuration file loading and management."""

    __slots__ = ("config", "path")

    def __init__(self, path: Path = None) -> None:
        """Initialize the LogseqAnalyzerConfig class."""
        self.path: Path = path
        self.config: configparser.ConfigParser = self.initialize_configparser()

    def __getitem__(self, section: str) -> dict[str, str]:
        """Get a section from the config file as a dictionary."""
        if section not in self.config:
            return {}
        return dict(self.config[section])

    def initialize_configparser(self) -> configparser.ConfigParser:
        """Initialize a ConfigParser with custom settings."""
        config = configparser.ConfigParser(
            allow_no_value=True,
            inline_comment_prefixes=("#", ";"),
            default_section="",
            interpolation=configparser.ExtendedInterpolation(),
            empty_lines_in_values=False,
            allow_unnamed_section=True,
        )
        config.optionxform = lambda_optionxform
        config.read(self.path)
        return config

    def set_value(self, section, key, value) -> None:
        """set a value in the config file"""
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def write_to_file(self, output_path: Path = None) -> None:
        """Write the config to a file"""
        with open(output_path, "w", encoding="utf-8") as file:
            self.config.write(file)

    def set_logseq_config_edn_data(self, target_dirs: dict[str, str]) -> None:
        """set the Logseq configuration data."""
        self.set_value("LOGSEQ_CONFIG", Config.DIR_PAGES.value, target_dirs["pages"])
        self.set_value("LOGSEQ_CONFIG", Config.DIR_JOURNALS.value, target_dirs["journals"])
        self.set_value("LOGSEQ_CONFIG", Config.DIR_WHITEBOARDS.value, target_dirs["whiteboards"])

    @property
    def config_dict(self) -> dict[str, dict[str, str]]:
        """Get the configuration as a dictionary."""
        config_dict = {}
        for section in self.config.sections():
            if repr(section) == "<UNNAMED_SECTION>":
                continue
            config_dict[section] = {}
            for key, value in self.config[section].items():
                config_dict[section][key] = value
        return config_dict

    @property
    def report(self) -> dict[str, str]:
        """Get a report of the configuration settings."""
        return {
            Output.ANALYZER_CONFIG.value: {
                Output.AC_CONFIG.value: self.config_dict,
            }
        }
