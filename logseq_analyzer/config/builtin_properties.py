"""
Logseq Built-in Properties Module
"""

from typing import Dict, List

from .analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import singleton


@singleton
class LogseqBuiltInProperties:
    """
    A class to handle built-in properties for Logseq.
    """

    def __init__(self):
        """Initialize the LogseqBuiltInProperties class."""
        self.analyzer_config = LogseqAnalyzerConfig()
        self.built_in_properties = None
        self.set_builtin_properties()

    def set_builtin_properties(self):
        """Build the built-in properties set."""
        properties_str = self.analyzer_config.config["BUILT_IN_PROPERTIES"]["PROPERTIES"]
        self.built_in_properties = frozenset(properties_str.split(","))

    def split_builtin_user_properties(self, properties: list) -> Dict[str, List[str]]:
        """
        Helper function to split properties into built-in and user-defined.

        Args:
            properties (list): List of properties to split.

        Returns:
            Dict[str, List[str]]: Dictionary containing built-in and user-defined properties.
        """
        properties_dict = {
            "built_in": [prop for prop in properties if prop in self.built_in_properties],
            "user_props": [prop for prop in properties if prop not in self.built_in_properties],
        }
        return properties_dict
