"""
Logseq Graph Class
"""

from pathlib import Path
import logging

from .helpers import get_file_or_folder
from .logseq_config_edn import loads
from .logseq_analyzer_config import LogseqAnalyzerConfig, ANALYZER_CONFIG
from .logseq_analyzer import LogseqAnalyzer, ANALYZER

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

    def __init__(self, analyzer_config: LogseqAnalyzerConfig, analyzer: LogseqAnalyzer):
        """Initialize the LogseqGraphConfig class."""
        self.analyzer_config = analyzer_config
        self.analyzer = analyzer
        self.directory = Path()
        self.logseq_dir = Path()
        self.recycle_dir = Path()
        self.bak_dir = Path()
        self.user_config_file = Path()
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
        self.directory = get_file_or_folder(self.analyzer.args.graph_folder)
        logging.info("Graph directory: %s", self.directory)

        self.logseq_dir = get_file_or_folder(self.directory / self.analyzer_config.get("CONST", "LOGSEQ_DIR"))
        logging.info("Logseq directory: %s", self.logseq_dir)

        self.recycle_dir = get_file_or_folder(self.logseq_dir / self.analyzer_config.get("CONST", "RECYCLE_DIR"))
        logging.info("Recycle directory: %s", self.recycle_dir)

        self.bak_dir = get_file_or_folder(self.logseq_dir / self.analyzer_config.get("CONST", "BAK_DIR"))
        logging.info("Bak directory: %s", self.bak_dir)

        self.user_config_file = get_file_or_folder(self.logseq_dir / self.analyzer_config.get("CONST", "CONFIG_FILE"))
        logging.info("User config file: %s", self.user_config_file)

    def initialize_config(self) -> None:
        """Initialize the Logseq configuration."""
        self.ls_config = LOGSEQ_DEFAULT_CONFIG_EDN_DATA
        with self.user_config_file.open("r", encoding="utf-8") as f:
            self.ls_config.update(loads(f.read()))

        if self.analyzer.args.global_config:
            self.analyzer_config.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", self.analyzer.args.global_config)
            global_config_file = get_file_or_folder(Path(self.analyzer.args.global_config))
            logging.info("Global config file: %s", global_config_file)
            with global_config_file.open("r", encoding="utf-8") as f:
                self.ls_config.update(loads(f.read()))


GRAPH_CONFIG = LogseqGraphConfig(ANALYZER_CONFIG, ANALYZER)
