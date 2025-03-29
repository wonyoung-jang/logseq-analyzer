"""
Logseq Analyzer Class
"""

import logging
import shutil
from pathlib import Path


from .config_loader import Config

CONFIG = Config.get_instance()


class LogseqAnalyzer:
    """
    A class to analyze Logseq data.
    """

    instance = None

    def __init__(self):
        """Initialize the LogseqAnalyzer."""
        self.output_dir = Path()
        self.log_file = Path()
        self.delete_dir = Path()
        self.create_output_directory()
        self.create_log_file()
        self.create_delete_directory()

    @staticmethod
    def get_instance():
        """Get the singleton instance of LogseqAnalyzer."""
        if LogseqAnalyzer.instance is None:
            LogseqAnalyzer.instance = LogseqAnalyzer()
        return LogseqAnalyzer.instance

    def create_output_directory(self) -> None:
        """Setup the output directory for the Logseq Analyzer."""
        self.output_dir = Path(CONFIG.get("ANALYZER", "OUTPUT_DIR"))

        if self.output_dir.exists() and self.output_dir.is_dir():
            try:
                shutil.rmtree(self.output_dir)
                logging.info("Removed existing output directory: %s", self.output_dir)
            except IsADirectoryError:
                logging.error("Output directory is not empty: %s", self.output_dir)

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logging.info("Created output directory: %s", self.output_dir)
        except FileExistsError:
            logging.error("Output directory already exists: %s", self.output_dir)
        except PermissionError:
            logging.error("Permission denied to create output directory: %s", self.output_dir)
        except OSError as e:
            logging.error("Error creating output directory: %s", e)

    def create_log_file(self) -> None:
        """Setup logging configuration for the Logseq Analyzer."""
        log_path = CONFIG.get("ANALYZER", "LOG_FILE")
        self.log_file = Path(self.output_dir / log_path)

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

    def create_delete_directory(self) -> Path:
        """
        Create a directory for deleted files.

        Returns:
            Path: The path to the delete directory.
        """
        self.delete_dir = Path(CONFIG.get("ANALYZER", "TO_DELETE_DIR"))
        if not self.delete_dir.exists():
            logging.info("Creating directory: %s", self.delete_dir)
            self.delete_dir.mkdir(parents=True, exist_ok=True)
        return self.delete_dir
