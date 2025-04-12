"""
Logseq Graph Class
"""

from .edn_parser import loads
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
            self.user_config_file = None
            self.global_config_file = None

    def initialize_config_edns(self):
        """Initialize the Logseq configuration."""
        with self.user_config_file.open("r", encoding="utf-8") as user_config:
            parsed_user_config = loads(user_config.read())
            self.ls_config.update(parsed_user_config)

        if self.global_config_file:
            with self.global_config_file.open("r", encoding="utf-8") as global_config:
                parsed_global_config = loads(global_config.read())
                self.ls_config.update(parsed_global_config)
