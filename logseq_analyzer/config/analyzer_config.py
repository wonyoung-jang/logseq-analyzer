"""
Config class for loading and managing configuration files.
"""

import configparser
import logging
from pathlib import Path

from ..utils.enums import Core
from ..utils.helpers import singleton


def lambda_optionxform(option: str) -> str:
    """
    Custom optionxform function to preserve case sensitivity of options.
    """
    return option


@singleton
class LogseqAnalyzerConfig:
    """A class to handle configuration file loading and management."""

    __slots__ = ("config", "target_dirs")

    def __init__(self, config_path: Path = Path("configuration/config.ini")) -> None:
        """Initialize the LogseqAnalyzerConfig class."""
        if not config_path.exists():
            logging.error("Configuration file not found: %s", config_path)
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        config = configparser.ConfigParser(
            allow_no_value=True,
            inline_comment_prefixes=("#", ";"),
            default_section="",
            interpolation=configparser.ExtendedInterpolation(),
            empty_lines_in_values=False,
            allow_unnamed_section=True,
        )
        config.optionxform = lambda_optionxform
        config.read(config_path)
        self.config = config
        self.target_dirs = set()

    def get(self, section, key, fallback=None) -> str | None:
        """Get a value from the config file"""
        return self.config.get(section, key, fallback=fallback)

    def set_value(self, section, key, value) -> None:
        """set a value in the config file"""
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def get_section(self, section) -> dict[str, str]:
        """Get a section from the config file as a dictionary"""
        if section not in self.config:
            return {}
        return dict(self.config[section])

    def write_to_file(self, output_path: Path = Path("configuration/user_config.ini")) -> None:
        """Write the config to a file"""
        with open(output_path, "w", encoding="utf-8") as file:
            self.config.write(file)

    def set_logseq_config_edn_data(self, graph_config: dict[str, str]) -> None:
        """set the Logseq configuration data."""
        self.set_value("LOGSEQ_CONFIG", "DIR_PAGES", graph_config.get(":pages-directory", "pages"))
        self.set_value("LOGSEQ_CONFIG", "DIR_JOURNALS", graph_config.get(":journals-directory", "journals"))
        self.set_value("LOGSEQ_CONFIG", "DIR_WHITEBOARDS", graph_config.get(":whiteboards-directory", "whiteboards"))

        ns_format = graph_config.get(":file/name-format", Core.NS_CONFIG_TRIPLE_LOWBAR.value)
        self.set_value("LOGSEQ_CONFIG", "NAMESPACE_FORMAT", ns_format)

        if ns_format == Core.NS_CONFIG_LEGACY.value:
            self.set_value("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", Core.NS_FILE_SEP_LEGACY.value)
        elif ns_format == Core.NS_CONFIG_TRIPLE_LOWBAR.value:
            self.set_value("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", Core.NS_FILE_SEP_TRIPLE_LOWBAR.value)

    def set_logseq_target_dirs(self) -> None:
        """Get the target directories based on the configuration data."""
        config = self.get_section("LOGSEQ_CONFIG")
        self.target_dirs = {
            config["DIR_ASSETS"],
            config["DIR_DRAWS"],
            config["DIR_PAGES"],
            config["DIR_JOURNALS"],
            config["DIR_WHITEBOARDS"],
        }
