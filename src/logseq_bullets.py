import logging
from pathlib import Path


class LogseqBullets:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = ""
        self.char_count = 0

    def get_content(self):
        """Read the text content of a file."""
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logging.warning("File not found: %s", self.file_path)
        except IsADirectoryError:
            logging.warning("Path is a directory, not a file: %s", self.file_path)
        except UnicodeDecodeError:
            logging.warning("Failed to decode file %s with utf-8 encoding.", self.file_path)

    def get_char_count(self):
        if self.content:
            self.char_count = len(self.content)
