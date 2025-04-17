"""
Path Validator for Logseq Analyzer
"""

from ..utils.helpers import singleton
from ..config.analyzer_config import LogseqAnalyzerConfig
from .filesystem import File


@singleton
class LogseqAnalyzerPathValidator:
    """Class to validate paths in the Logseq analyzer."""

    def __init__(self):
        """Initialize the path validator."""
        self._ac = LogseqAnalyzerConfig()
        # 01 Output and Logging
        self.dir_output = None
        self.file_log = None
        # 02 Graph and Logseq Config - required for config.edn to get target paths
        self.dir_graph = None
        self.dir_logseq = None
        self.file_config = None
        # 03 Analyzer Paths - required for deleting files
        self.dir_delete = None
        self.dir_delete_bak = None
        self.dir_delete_recycle = None
        self.dir_delete_assets = None
        # 04 Graph Paths - required for deleting files
        self.dir_recycle = None
        self.dir_bak = None
        # 05 Target Paths - required for analyzing files
        self.dir_assets = None
        self.dir_draws = None
        self.dir_journals = None
        self.dir_pages = None
        self.dir_whiteboards = None
        # 06 Global Config Path
        self.file_config_global = None
        # 07 Cache Path
        self.file_cache = None

    def validate_cache(self):
        """Validate the cache file."""
        self.file_cache = File(self._ac.config["CONST"]["CACHE"])

    def validate_output_dir_and_logging(self):
        """Validate the output directory and logging."""
        self.dir_output = File(self._ac.config["CONST"]["OUTPUT_DIR"])
        self.file_log = File(self._ac.config["CONST"]["LOG_FILE"])
        self.dir_output.initialize_dir()  # Clear all and create
        self.file_log.initialize_file()  # Delete and create

    def validate_graph_logseq_config_paths(self):
        """Validate the graph and Logseq configuration paths."""
        self.dir_graph = File(self._ac.config["ANALYZER"]["GRAPH_DIR"])
        self.dir_logseq = File(self._ac.config["CONST"]["LOGSEQ_DIR"])
        self.file_config = File(self._ac.config["CONST"]["CONFIG_FILE"])
        self.dir_graph.validate()  # Must exist
        self.dir_logseq.validate()  # Must exist
        self.file_config.validate()  # Must exist

    def validate_analyzer_paths(self):
        """Validate the analyzer paths."""
        self.dir_delete = File(self._ac.config["CONST"]["TO_DELETE_DIR"])
        self.dir_delete_bak = File(self._ac.config["CONST"]["TO_DELETE_BAK_DIR"])
        self.dir_delete_recycle = File(self._ac.config["CONST"]["TO_DELETE_RECYCLE_DIR"])
        self.dir_delete_assets = File(self._ac.config["CONST"]["TO_DELETE_ASSETS_DIR"])
        self.dir_delete.get_or_create_dir()  # Create if it doesn't exist
        self.dir_delete_bak.get_or_create_dir()  # Create if it doesn't exist
        self.dir_delete_recycle.get_or_create_dir()  # Create if it doesn't exist
        self.dir_delete_assets.get_or_create_dir()  # Create if it doesn't exist

    def validate_graph_paths(self):
        """Validate the graph paths."""
        self.dir_recycle = File(self._ac.config["CONST"]["RECYCLE_DIR"])
        self.dir_bak = File(self._ac.config["CONST"]["BAK_DIR"])
        self.dir_recycle.get_or_create_dir()  # Create if it doesn't exist
        self.dir_bak.get_or_create_dir()  # Create if it doesn't exist

    def validate_target_paths(self):
        """Validate the target paths."""
        self.dir_assets = File(self._ac.config["TARGET_DIRS"]["DIR_ASSETS"])
        self.dir_draws = File(self._ac.config["TARGET_DIRS"]["DIR_DRAWS"])
        self.dir_journals = File(self._ac.config["TARGET_DIRS"]["DIR_JOURNALS"])
        self.dir_pages = File(self._ac.config["TARGET_DIRS"]["DIR_PAGES"])
        self.dir_whiteboards = File(self._ac.config["TARGET_DIRS"]["DIR_WHITEBOARDS"])
        self.dir_assets.get_or_create_dir()  # Create if it doesn't exist
        self.dir_draws.get_or_create_dir()  # Create if it doesn't exist
        self.dir_journals.get_or_create_dir()  # Create if it doesn't exist
        self.dir_pages.get_or_create_dir()  # Create if it doesn't exist
        self.dir_whiteboards.get_or_create_dir()  # Create if it doesn't exist

    def validate_global_config_path(self):
        """Validate the global configuration file path."""
        self.file_config_global = File(self._ac.config["LOGSEQ_FILESYSTEM"]["GLOBAL_CONFIG_FILE"])
        self.file_config_global.validate()  # Must exist
