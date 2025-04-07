"""
Logseq Graph Class
"""

from pathlib import Path
import logging

from ._global_objects import ANALYZER_CONFIG
from .helpers import get_file_or_folder
from .logseq_config_edn import LogseqConfigEDN

LOGSEQ_DEFAULT_CONFIG_EDN_DATA = {
    "journal_page_title_format": "MMM do, yyyy",
    "journal_file_name_format": "yyyy_MM_dd",
    "journals_directory": "journals",
    "pages_directory": "pages",
    "whiteboards_directory": "whiteboards",
    "file_name_format": ":legacy",
}


class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    def __init__(self):
        """Initialize the LogseqGraphConfig class."""
        self.directory = Path()
        self.logseq_dir = Path()
        self.recycle_dir = Path()
        self.bak_dir = Path()
        self.user_config_file = Path()
        self.ls_config = {}

    def initialize_graph(self, graph_folder) -> None:
        """
        Initialize the Logseq graph directories.

        graph/
        ├── logseq/
            ├── .recycle/
            ├── bak/
            ├── config.edn
        """
        self.directory = get_file_or_folder(graph_folder)
        logging.info("Graph directory: %s", self.directory)
        self.logseq_dir = get_file_or_folder(self.directory / ANALYZER_CONFIG.get("CONST", "LOGSEQ_DIR"))
        logging.info("Logseq directory: %s", self.logseq_dir)
        self.recycle_dir = get_file_or_folder(self.logseq_dir / ANALYZER_CONFIG.get("CONST", "RECYCLE_DIR"))
        logging.info("Recycle directory: %s", self.recycle_dir)
        self.bak_dir = get_file_or_folder(self.logseq_dir / ANALYZER_CONFIG.get("CONST", "BAK_DIR"))
        logging.info("Bak directory: %s", self.bak_dir)
        self.user_config_file = get_file_or_folder(self.logseq_dir / ANALYZER_CONFIG.get("CONST", "CONFIG_FILE"))
        logging.info("User config file: %s", self.user_config_file)

    def initialize_config(self, args) -> None:
        """Initialize the Logseq configuration."""
        user_config = LogseqConfigEDN(args, self.user_config_file)
        user_config.clean_logseq_config_edn_content()
        user_config.get_config_edn_data_for_analysis()
        self.ls_config = LOGSEQ_DEFAULT_CONFIG_EDN_DATA
        self.ls_config.update(user_config.config_edn_data)
        del user_config
        if args.global_config:
            global_config_file = get_file_or_folder(Path(args.global_config))
            logging.info("Global config file: %s", global_config_file)
            ANALYZER_CONFIG.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", args.global_config)
            global_config = LogseqConfigEDN(args, global_config_file)
            global_config.clean_logseq_config_edn_content()
            global_config.get_config_edn_data_for_analysis()
            self.ls_config.update(global_config.config_edn_data)
            del global_config
