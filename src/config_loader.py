import configparser
import os
import re


class Config:
    def __init__(self, config_path="src/config.ini"):
        self.config = configparser.ConfigParser(
            allow_no_value=True,
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

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set(self, section, key, value):
        if section not in self.config:
            self.config.add_section(section)
        self.config.set(section, key, value)

    def get_section(self, section):
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


# Singleton
_config_instance = None


def get_config(config_path="src/config.ini"):
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance
