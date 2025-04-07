"""
Logseq configuration module.
"""

from pathlib import Path
import argparse
import logging

from ._global_objects import PATTERNS


class LogseqConfigEDN:
    """
    A class to handle Logseq configuration data.
    """

    def __init__(self, args: argparse.Namespace, config_file: Path):
        """Initialize the LogseqConfigEDN class."""
        self.args = args
        self.config_file = config_file
        self.config_edn_content = ""
        self.config_edn_data = {}

    def clean_logseq_config_edn_content(self):
        """Extract EDN configuration data from a Logseq configuration file."""
        with self.config_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(";"):
                    continue
                if ";" in line:
                    line = line.split(";")[0].strip()
                self.config_edn_content += f"{line}\n"

    def get_config_edn_data_for_analysis(self):
        """Extract EDN configuration data from a Logseq configuration file."""
        if not self.config_edn_content:
            logging.warning("No config.edn content found.")
            return

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
