"""
Logseq Analyzer Class
"""

import argparse
from pathlib import Path
import logging
import shutil

from .helpers import get_or_create_file_or_folder


class LogseqAnalyzer:
    """
    A class to analyze Logseq data.
    """

    def __init__(self, analyzer_config):
        """Initialize the LogseqAnalyzer class."""
        self.analyzer_config = analyzer_config
        self.args = None
        self.output_dir = None
        self.log_file = None
        self.delete_dir = None
        self.get_built_in_properties()
        self.get_datetime_token_map()
        self.get_datetime_token_pattern()

    def create_output_directory(self):
        """Setup the output directory for the Logseq Analyzer."""
        self.output_dir = Path(self.analyzer_config.get("ANALYZER", "OUTPUT_DIR"))
        if self.output_dir.exists():
            try:
                shutil.rmtree(self.output_dir)
                logging.info("Removed existing output directory: %s", self.output_dir)
                self.output_dir = get_or_create_file_or_folder(self.output_dir)
            except PermissionError:
                logging.error("Permission denied to remove output directory: %s", self.output_dir)

    def create_log_file(self):
        """Setup logging configuration for the Logseq Analyzer."""
        self.log_file = Path(self.output_dir) / self.analyzer_config.get("ANALYZER", "LOG_FILE")
        if self.log_file.exists():
            self.log_file.unlink()
        logging.basicConfig(
            filename=self.log_file,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            encoding="utf-8",
            datefmt="%Y-%m-%d %H:%M:%S",
            force=True,
        )
        logging.debug("Logging initialized to %s", self.log_file)
        logging.info("Logseq Analyzer started.")

    def create_delete_directory(self):
        """
        Create a directory for deleted files.
        """
        self.delete_dir = get_or_create_file_or_folder(Path(self.analyzer_config.get("ANALYZER", "TO_DELETE_DIR")))

    def get_logseq_analyzer_args(self, **kwargs: dict):
        """
        Setup the command line arguments for the Logseq Analyzer.
        """
        if kwargs:
            args = argparse.Namespace(
                graph_folder=kwargs.get("graph_folder"),
                global_config=kwargs.get("global_config_file"),
                move_unlinked_assets=kwargs.get("move_assets", False),
                move_bak=kwargs.get("move_bak", False),
                move_recycle=kwargs.get("move_recycle", False),
                write_graph=kwargs.get("write_graph", False),
                graph_cache=kwargs.get("graph_cache", False),
                report_format=kwargs.get("report_format", ""),
            )
            self.args = args
        else:
            parser = argparse.ArgumentParser(description="Logseq Analyzer")

            parser.add_argument(
                "-g",
                "--graph-folder",
                action="store",
                help="path to your main Logseq graph folder (contains subfolders)",
                required=True,
            )
            parser.add_argument(
                "-wg",
                "--write-graph",
                action="store_true",
                help="write all graph content to output folder (warning: may result in large file)",
            )
            parser.add_argument(
                "--graph-cache",
                action="store_true",
                help="reindex graph cache on run",
            )
            parser.add_argument(
                "-ma",
                "--move-unlinked-assets",
                action="store_true",
                help='move unlinked assets to "unlinked_assets" folder',
            )
            parser.add_argument(
                "-mb",
                "--move-bak",
                action="store_true",
                help="move bak files to bak folder in output directory",
            )
            parser.add_argument(
                "-mr",
                "--move-recycle",
                action="store_true",
                help="move recycle files to recycle folder in output directory",
            )
            parser.add_argument(
                "--global-config",
                action="store",
                help="path to global configuration file",
            )
            parser.add_argument(
                "--report-format",
                action="store",
                help="report format (.txt, .json)",
            )

            self.args = parser.parse_args()
