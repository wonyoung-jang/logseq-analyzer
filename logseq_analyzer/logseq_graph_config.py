"""
Logseq Graph Class
"""

from pathlib import Path
import logging

from .helpers import get_file_or_folder
from .logseq_config_edn import loads
from .logseq_analyzer_config import LogseqAnalyzerConfig
from .logseq_analyzer import LogseqAnalyzer

ANALYZER_CONFIG = LogseqAnalyzerConfig()
ANALYZER = LogseqAnalyzer()

LOGSEQ_DEFAULT_CONFIG_EDN_DATA = {
    ":journal/page-title-format": "MMM do, yyyy",
    ":journal/file-name-format": "yyyy_MM_dd",
    ":journals-directory": "journals",
    ":pages-directory": "pages",
    ":whiteboards-directory": "whiteboards",
    ":file/name-format": ":legacy",
}


class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LogseqGraphConfig class."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.directory = None
            self.logseq_dir = None
            self.recycle_dir = None
            self.bak_dir = None
            self.user_config_file = None
            self.ls_config = {}

    def initialize_graph(self) -> None:
        """
        Initialize the Logseq graph directories.

        graph/
        ├── logseq/
            ├── .recycle/
            ├── bak/
            ├── config.edn
        """
        self.directory = get_file_or_folder(ANALYZER.args.graph_folder)
        logging.info("Graph directory: %s", self.directory)

        self.logseq_dir = get_file_or_folder(self.directory / ANALYZER_CONFIG.config["CONST"]["LOGSEQ_DIR"])
        logging.info("Logseq directory: %s", self.logseq_dir)

        self.recycle_dir = get_file_or_folder(self.logseq_dir / ANALYZER_CONFIG.config["CONST"]["RECYCLE_DIR"])
        logging.info("Recycle directory: %s", self.recycle_dir)

        self.bak_dir = get_file_or_folder(self.logseq_dir / ANALYZER_CONFIG.config["CONST"]["BAK_DIR"])
        logging.info("Bak directory: %s", self.bak_dir)

        self.user_config_file = get_file_or_folder(self.logseq_dir / ANALYZER_CONFIG.config["CONST"]["CONFIG_FILE"])
        logging.info("User config file: %s", self.user_config_file)

    def initialize_config(self) -> None:
        """Initialize the Logseq configuration."""
        self.ls_config = LOGSEQ_DEFAULT_CONFIG_EDN_DATA
        with self.user_config_file.open("r", encoding="utf-8") as f:
            self.ls_config.update(loads(f.read()))

        if ANALYZER.args.global_config:
            ANALYZER_CONFIG.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", ANALYZER.args.global_config)
            global_config_file = get_file_or_folder(Path(ANALYZER.args.global_config))
            logging.info("Global config file: %s", global_config_file)
            with global_config_file.open("r", encoding="utf-8") as f:
                self.ls_config.update(loads(f.read()))
