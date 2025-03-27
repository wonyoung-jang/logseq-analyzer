"""
Config class for loading and managing configuration files.
"""

import configparser
import os
import re


class Config:
    """
    A class to handle configuration file loading and management.

    This class uses the configparser module to read and write configuration files.
    It provides methods to get and set configuration values, as well as to retrieve
    specific sections and properties from the configuration file.

    Attributes:
        config (configparser.ConfigParser): The configparser instance for handling the configuration file.
        _datetime_token_map (dict): A dictionary mapping datetime tokens to their values.
        _datetime_token_pattern (re.Pattern): A compiled regex pattern for datetime tokens.
        _built_in_properties (frozenset): A frozenset of built-in properties defined in the configuration file.
    """

    instance = None

    def __init__(self, config_path="src/config.ini"):
        """
        Initialize the Config class with a given config file path.
        If the file does not exist, a FileNotFoundError is raised.
        """
        self.config = configparser.ConfigParser(
            allow_no_value=True,
            inline_comment_prefixes=("#", ";"),
            default_section="None",
            interpolation=configparser.ExtendedInterpolation(),
        )

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")

        self.config.optionxform = lambda option: option
        self.config.read(config_path)

        self._datetime_token_map = None
        self._datetime_token_pattern = None
        self._built_in_properties = None

    @staticmethod
    def get_instance(config_path="src/config.ini"):
        """
        Get the singleton instance of the Config class.
        """
        if Config.instance is None:
            Config.instance = Config(config_path)
        return Config.instance

    def get(self, section, key, fallback=None):
        """Get a value from the config file"""
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        """Set a value in the config file"""
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, value)

    def get_section(self, section):
        """Get a section from the config file as a dictionary"""
        if section in self.config:
            return dict(self.config[section])
        return {}

    def get_datetime_token_map(self):
        """Return the datetime token mapping as a dictionary"""
        if self._datetime_token_map is None:
            self._datetime_token_map = self.get_section("DATETIME_TOKEN_MAP")
        return self._datetime_token_map

    def get_datetime_token_pattern(self):
        """Return a compiled regex pattern for datetime tokens"""
        if self._datetime_token_pattern is None:
            tokens = self.get_datetime_token_map().keys()
            pattern = "|".join(re.escape(k) for k in sorted(tokens, key=len, reverse=True))
            self._datetime_token_pattern = re.compile(pattern)
        return self._datetime_token_pattern

    def get_built_in_properties(self):
        """Return the built-in properties as a frozenset"""
        if self._built_in_properties is None:
            properties_str = self.get("BUILT_IN_PROPERTIES", "PROPERTIES")
            self._built_in_properties = frozenset(properties_str.split(","))
        return self._built_in_properties

    def write(self, file):
        """Write the config to a file-like object"""
        self.config.write(file)


def get_config():
    """
    Get the singleton instance of the Config class.
    """
    return Config.get_instance()
