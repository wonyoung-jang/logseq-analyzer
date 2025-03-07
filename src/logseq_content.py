import logging
from pathlib import Path


class LogseqContent:
    def __init__(self, name: str, name_secondary: str, content: str):
        self.name = name
        self.name_secondary = name_secondary
        self.content = content