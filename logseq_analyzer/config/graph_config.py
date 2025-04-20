"""
Logseq Graph Class
"""

from ..utils.helpers import singleton
from .edn_parser import loads
from .default_logseq_config_edn import DEFAULT_LOGSEQ_CONFIG_EDN


@singleton
class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    def __init__(self):
        """Initialize the LogseqGraphConfig class."""
        self.ls_config = None
        self.user_config_file = None
        self.user_config_data = {}
        self.global_config_file = None
        self.global_config_data = {}

    def initialize_user_config_edn(self):
        """Extract user config."""
        with self.user_config_file.open("r", encoding="utf-8") as user_config:
            self.user_config_data = loads(user_config.read())

    def initialize_global_config_edn(self):
        """Extract global config."""
        if not self.global_config_file:
            return

        with self.global_config_file.open("r", encoding="utf-8") as global_config:
            self.global_config_data = loads(global_config.read())

    def merge(self):
        """Merge user and global config."""
        self.ls_config = DEFAULT_LOGSEQ_CONFIG_EDN
        self.ls_config.update(self.user_config_data)
        self.ls_config.update(self.global_config_data)
