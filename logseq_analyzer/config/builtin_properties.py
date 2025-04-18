"""
Logseq Built-in Properties Module
"""

from dataclasses import dataclass
from typing import Dict, List

from .analyzer_config import LogseqAnalyzerConfig
from ..utils.helpers import singleton


@singleton
@dataclass
class LogseqBuiltInProperties:
    """
    A class to handle built-in properties for Logseq.
    """

    built_in_properties: frozenset = frozenset()

    def __post_init__(self):
        """Build the built-in properties set."""
        properties_str = LogseqAnalyzerConfig().config["BUILT_IN_PROPERTIES"]["PROPERTIES"]
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
