"""
Logseq Built-in Properties Module
"""

from ..utils.helpers import singleton
from .analyzer_config import LogseqAnalyzerConfig


@singleton
class LogseqBuiltInProperties:
    """
    A class to handle built-in properties for Logseq.
    """

    __slots__ = ("built_in_properties",)

    def __init__(self) -> None:
        """Build the built-in properties set."""
        lac = LogseqAnalyzerConfig()
        properties_str = lac.config["BUILT_IN_PROPERTIES"]["PROPERTIES"]
        self.built_in_properties: frozenset = frozenset(properties_str.split(","))


def split_builtin_user_properties(properties: list[str]) -> dict[str, list[str]]:
    """
    Helper function to split properties into built-in and user-defined.

    Args:
        properties (list[str]): List of properties to split.

    Returns:
        dict[str, list[str]]: Dictionary containing built-in and user-defined properties.
    """
    lsbip = LogseqBuiltInProperties()
    built_ins = lsbip.built_in_properties
    properties_dict = {
        "built_ins": [prop for prop in properties if prop in built_ins],
        "user_props": [prop for prop in properties if prop not in built_ins],
    }
    return properties_dict
