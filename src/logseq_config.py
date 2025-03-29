"""
Logseq configuration module.
"""

import argparse
import logging
from pathlib import Path

from src.config_loader import Config
from src.compile_regex import RegexPatterns

PATTERNS = RegexPatterns.get_instance()
CONFIG = Config.get_instance()


class LogseqConfig:
    """
    A class to handle Logseq configuration data.
    """

    def __init__(self, args: argparse.Namespace, config_file: Path):
        """Initialize the LogseqConfig class."""
        self.args = args
        self.config_edn_content = None
        self.config_edn_data = None
        self.clean_logseq_config_edn_content(config_file)
        self.get_config_edn_data_for_analysis()

    def clean_logseq_config_edn_content(self, config_file: Path) -> str:
        """
        Extract EDN configuration data from a Logseq configuration file.

        Args:
            folder_path (Path): The path to the Logseq graph folder.

        Returns:
            str: The content of the configuration file.
        """
        with config_file.open("r", encoding="utf-8") as f:
            self.config_edn_content = ""
            for line in f.readlines():
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                if ";" in line:
                    line = line.split(";")[0].strip()
                self.config_edn_content += f"{line}\n"

    def get_config_edn_data_for_analysis(self):
        """
        Extract EDN configuration data from a Logseq configuration file.

        Returns:
            dict: A dictionary containing the extracted configuration data.
        """
        if not self.config_edn_content:
            logging.warning("No config.edn content found.")
            self.config_edn_data = {}

        config_edn_data = {
            "journal_page_title_format": None,
            "journal_file_name_format": None,
            "journals_directory": None,
            "pages_directory": None,
            "whiteboards_directory": None,
            "file_name_format": None,
        }

        for key in config_edn_data:
            pattern = PATTERNS.config.get(f"{key}_pattern")
            if pattern:
                match = pattern.search(self.config_edn_content)
                if match:
                    config_edn_data[key] = match.group(1)

        self.config_edn_data = {k: v for k, v in config_edn_data.items() if v is not None}
