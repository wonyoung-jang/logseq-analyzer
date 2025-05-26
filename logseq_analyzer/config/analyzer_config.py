"""
Config class for loading and managing configuration files.
"""

import configparser
from pathlib import Path

from ..utils.enums import Core, Config, Output
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

    def __init__(self, config_path: Path = None) -> None:
        """Initialize the LogseqAnalyzerConfig class."""
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

    def __getitem__(self, section: str) -> dict[str, str]:
        """Get a section from the config file as a dictionary."""
        if section not in self.config:
            return {}
        return dict(self.config[section])

    def set_value(self, section, key, value) -> None:
        """set a value in the config file"""
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, str(value))

    def write_to_file(self, output_path: Path = None) -> None:
        """Write the config to a file"""
        with open(output_path, "w", encoding="utf-8") as file:
            self.config.write(file)

    def set_logseq_config_edn_data(self, graph_config: dict[str, str]) -> None:
        """set the Logseq configuration data."""
        edn_pages_dir = graph_config.get(":pages-directory", "pages")
        edn_journals_dir = graph_config.get(":journals-directory", "journals")
        edn_whiteboards_dir = graph_config.get(":whiteboards-directory", "whiteboards")
        ns_format = graph_config.get(":file/name-format", Core.NS_CONFIG_TRIPLE_LOWBAR.value)
        self.set_value("LOGSEQ_CONFIG", Config.DIR_PAGES.value, edn_pages_dir)
        self.set_value("LOGSEQ_CONFIG", Config.DIR_JOURNALS.value, edn_journals_dir)
        self.set_value("LOGSEQ_CONFIG", Config.DIR_WHITEBOARDS.value, edn_whiteboards_dir)
        self.set_value("LOGSEQ_CONFIG", "NAMESPACE_FORMAT", ns_format)

        if ns_format == Core.NS_CONFIG_LEGACY.value:
            self.set_value("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", Core.NS_FILE_SEP_LEGACY.value)
        elif ns_format == Core.NS_CONFIG_TRIPLE_LOWBAR.value:
            self.set_value("LOGSEQ_NAMESPACES", "NAMESPACE_FILE_SEP", Core.NS_FILE_SEP_TRIPLE_LOWBAR.value)

    def set_logseq_target_dirs(self) -> None:
        """Get the target directories based on the configuration data."""
        config = self["LOGSEQ_CONFIG"]
        self.target_dirs.update(
            (
                config[Config.DIR_ASSETS.value],
                config[Config.DIR_DRAWS.value],
                config[Config.DIR_PAGES.value],
                config[Config.DIR_JOURNALS.value],
                config[Config.DIR_WHITEBOARDS.value],
            )
        )

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
                Output.AC_TARGET_DIRS.value: self.target_dirs,
                Output.AC_CONFIG.value: self.config_dict,
            }
        }
