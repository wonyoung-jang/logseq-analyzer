import configparser
import os

# Singleton instance
_config_instance = None


def get_config(config_path="src/config.ini"):
    global _config_instance
    if _config_instance is None:
        _config_instance = configparser.ConfigParser()
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        _config_instance.read(config_path)
    return _config_instance
