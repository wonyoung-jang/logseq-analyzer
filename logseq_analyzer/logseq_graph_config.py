"""
Logseq Graph Class
"""

from pathlib import Path

from .helpers import get_file_or_folder
from .logseq_config_edn import loads
from .logseq_analyzer_config import LogseqAnalyzerConfig
from .default_logseq_config_edn import DEFAULT_LOGSEQ_CONFIG_EDN


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
            self.ls_config = DEFAULT_LOGSEQ_CONFIG_EDN
            self.directory = None
            self.logseq_dir = None
            self.recycle_dir = None
            self.bak_dir = None
            self.user_config_file = None

    def initialize_graph_structure(self):
        """
        Initialize the Logseq graph directories.

        graph/
        ├── logseq/
            ├── .recycle/
            ├── bak/
            ├── config.edn
        """
        la_config = LogseqAnalyzerConfig()
        self.directory = get_file_or_folder(la_config.config["ANALYZER"]["GRAPH_DIR"])
        self.logseq_dir = get_file_or_folder(la_config.config["CONST"]["LOGSEQ_DIR"])
        self.recycle_dir = get_file_or_folder(la_config.config["CONST"]["RECYCLE_DIR"])
        self.bak_dir = get_file_or_folder(la_config.config["CONST"]["BAK_DIR"])
        self.user_config_file = get_file_or_folder(la_config.config["CONST"]["CONFIG_FILE"])

    def initialize_config_edns(self, global_config: str):
        """Initialize the Logseq configuration."""
        la_config = LogseqAnalyzerConfig()
        with self.user_config_file.open("r", encoding="utf-8") as user_config:
            parsed_user_config = loads(user_config.read())
            self.ls_config.update(parsed_user_config)

        if global_config:
            la_config.set("LOGSEQ_FILESYSTEM", "GLOBAL_CONFIG_FILE", global_config)
            global_config_file = get_file_or_folder(Path(global_config))
            with global_config_file.open("r", encoding="utf-8") as global_config:
                parsed_global_config = loads(global_config.read())
                self.ls_config.update(parsed_global_config)
