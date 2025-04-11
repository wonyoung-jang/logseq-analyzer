from .filesystem import File
from .logseq_analyzer_config import LogseqAnalyzerConfig


class LogseqAnalyzerPathValidator:
    """Class to validate paths in the Logseq analyzer."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the path validator."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._ac = LogseqAnalyzerConfig()

            self.dir_output = None
            self.dir_delete = None
            self.dir_delete_bak = None
            self.dir_delete_recycle = None
            self.dir_delete_assets = None
            self.file_log = None

            self.dir_graph = None
            self.dir_logseq = None
            self.dir_recycle = None
            self.dir_bak = None
            self.file_config = None

            self.dir_assets = None
            self.dir_draws = None
            self.dir_journals = None
            self.dir_pages = None
            self.dir_whiteboards = None

            self.file_config_global = None

            self.file_cache = None

    def initialize(self):
        """Initialize the path validator."""
        self.file_cache = File(self._ac.config["CONST"]["CACHE"])

    def validate_analyzer_paths(self):
        """Validate the analyzer paths."""
        self.dir_output = File(self._ac.config["CONST"]["OUTPUT_DIR"])
        self.dir_delete = File(self._ac.config["CONST"]["TO_DELETE_DIR"])
        self.dir_delete_bak = File(self._ac.config["CONST"]["TO_DELETE_BAK_DIR"])
        self.dir_delete_recycle = File(self._ac.config["CONST"]["TO_DELETE_RECYCLE_DIR"])
        self.dir_delete_assets = File(self._ac.config["CONST"]["TO_DELETE_ASSETS_DIR"])
        self.file_log = File(self._ac.config["CONST"]["LOG_FILE"])
        self.dir_output.initialize_dir()  # Clear all and create
        self.dir_delete.get_or_create_dir()  # Create if it doesn't exist
        self.dir_delete_bak.get_or_create_dir()  # Create if it doesn't exist
        self.dir_delete_recycle.get_or_create_dir()  # Create if it doesn't exist
        self.dir_delete_assets.get_or_create_dir()  # Create if it doesn't exist
        self.file_log.initialize_file()  # Delete and create

    def validate_graph_paths(self):
        """Validate the graph paths."""
        self.dir_graph = File(self._ac.config["ANALYZER"]["GRAPH_DIR"])
        self.dir_logseq = File(self._ac.config["CONST"]["LOGSEQ_DIR"])
        self.dir_recycle = File(self._ac.config["CONST"]["RECYCLE_DIR"])
        self.dir_bak = File(self._ac.config["CONST"]["BAK_DIR"])
        self.file_config = File(self._ac.config["CONST"]["CONFIG_FILE"])
        self.dir_graph.validate()  # Must exist
        self.file_config.validate()  # Must exist
        self.dir_logseq.validate()  # Must exist
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
