"""
Logseq Graph Class
"""

from pathlib import Path
import logging

from ._global_objects import CONFIG
from .helpers import get_or_create_subdir, get_sub_file_or_folder
from .logseq_config import LogseqConfig

DEFAULT_LOGSEQ_DIRECTORY = CONFIG.get("LOGSEQ_FILESYSTEM", "LOGSEQ_DIR")
DEFAULT_RECYCLE_DIRECTORY = CONFIG.get("LOGSEQ_FILESYSTEM", "RECYCLE_DIR")
DEFAULT_BACKUP_DIRECTORY = CONFIG.get("LOGSEQ_FILESYSTEM", "BAK_DIR")
DEFAULT_CONFIG_FILE = CONFIG.get("LOGSEQ_FILESYSTEM", "CONFIG_FILE")
LOGSEQ_DEFAULT_CONFIG_EDN_DATA = {
    "journal_page_title_format": "MMM do, yyyy",
    "journal_file_name_format": "yyyy_MM_dd",
    "journals_directory": "journals",
    "pages_directory": "pages",
    "whiteboards_directory": "whiteboards",
    "file_name_format": ":legacy",
}


class LogseqGraph:
    """
    A class to LogseqGraph.
    """

    def __init__(self):
        """Initialize the LogseqGraph class."""
        self.directory = Path()
        self.logseq_dir = Path()
        self.recycle_dir = Path()
        self.bak_dir = Path()
        self.user_config_file = Path()
        self.global_config_file = Path()
        self.logseq_config = {}

    def initialize_config(self, args) -> None:
        """Initialize the Logseq configuration."""
        user_config = LogseqConfig(args, self.user_config_file)
        self.logseq_config = {**LOGSEQ_DEFAULT_CONFIG_EDN_DATA, **user_config.config_edn_data}
        if args.global_config:
            self.global_config_file = Path(args.global_config)
            if not self.global_config_file.exists():
                logging.warning("Global config file does not exist: %s", self.global_config_file)
                raise FileNotFoundError(f"Global config file does not exist: {self.global_config_file}") from None
            CONFIG.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", args.global_config)
            global_config = LogseqConfig(args, self.global_config_file)
            self.logseq_config.update(global_config.config_edn_data)

    def initialize_graph(self, args) -> None:
        """Initialize the Logseq graph directories."""
        self.validate_graph_dir(args)
        self.logseq_dir = get_or_create_subdir(self.directory, DEFAULT_LOGSEQ_DIRECTORY)
        self.recycle_dir = get_or_create_subdir(self.logseq_dir, DEFAULT_RECYCLE_DIRECTORY)
        self.bak_dir = get_or_create_subdir(self.logseq_dir, DEFAULT_BACKUP_DIRECTORY)
        self.user_config_file = get_sub_file_or_folder(self.logseq_dir, DEFAULT_CONFIG_FILE)

    def validate_graph_dir(self, args) -> Path:
        """Validate if a path exists."""
        path = args.graph_folder
        try:
            self.directory = Path(path).resolve(strict=True)
        except FileNotFoundError:
            logging.warning("Path does not exist: %s", path)
            raise FileNotFoundError(f"Path does not exist: {path}") from None
