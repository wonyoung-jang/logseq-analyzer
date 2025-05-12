"""
Config class for loading and managing configuration files.
"""

from pathlib import Path
import configparser
import logging

from ..utils.helpers import singleton
from ..utils.enums import Core


def lambda_optionxform(option: str) -> str:
    """
    Custom optionxform function to preserve case sensitivity of options.
    """
    return option


@singleton
class LogseqAnalyzerConfig:
    """A class to handle configuration file loading and management."""

    def __init__(self, config_path: Path = Path("configuration/config.ini")):
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
        self.config: configparser.ConfigParser = config
        self.target_dirs: set[str] = set()

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
        if section in self.config:
            return dict(self.config[section])
        return {}

    def write_to_file(self, output_path: Path = Path("configuration/user_config.ini")) -> None:
        """Write the config to a file"""
        with open(output_path, "w", encoding="utf-8") as file:
            self.config.write(file)

    def set_logseq_config_edn_data(self, ls_config: dict[str, str]) -> None:
        """set the Logseq configuration data."""
        config = self.config["LOGSEQ_CONFIG"]
        config["DIR_PAGES"] = ls_config.get(":pages-directory", "pages")
        config["DIR_JOURNALS"] = ls_config.get(":journals-directory", "journals")
        config["DIR_WHITEBOARDS"] = ls_config.get(":whiteboards-directory", "whiteboards")

        ns_format = ls_config.get(":file/name-format", ":legacy")
        config["NAMESPACE_FORMAT"] = ns_format
        if ns_format == ":triple-lowbar":
            self.config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"] = Core.NS_FILE_SEP_TRIPLE_LOWBAR.value

    def set_logseq_target_dirs(self) -> set[str]:
        """Get the target directories based on the configuration data."""
        config = self.config["LOGSEQ_CONFIG"]
        return {
            config["DIR_ASSETS"],
            config["DIR_DRAWS"],
            config["DIR_PAGES"],
            config["DIR_JOURNALS"],
            config["DIR_WHITEBOARDS"],
        }
