"""
Module for LogseqBullets class
"""

import logging
from pathlib import Path

from ._global_objects import PATTERNS


class LogseqBullets:
    """LogseqBullets class"""

    def __init__(self, file_path: Path):
        """Initialize the LogseqBullets class"""
        self.file_path = file_path
        self.content = ""
        self.primary_bullet = ""
        self.all_bullets = []
        self.content_bullets = []
        self.char_count = 0
        self.bullet_count = 0
        self.bullet_count_empty = 0
        self.bullet_density = 0
        self.get_content()
        self.get_char_count()
        self.get_bullet_content()
        self.get_primary_bullet()
        self.get_bullet_density()

    def get_content(self):
        """Read the text content of a file."""
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logging.warning("Failed to decode file %s with utf-8 encoding.", self.file_path)

    def get_char_count(self):
        """Get character count of content"""
        self.char_count = len(self.content)

    def get_bullet_content(self):
        """Get all bullets split into a list"""
        if self.content:
            self.all_bullets = PATTERNS.content["bullet"].split(self.content)

    def get_primary_bullet(self):
        """Get the Logseq primary bullet if available"""
        if len(self.all_bullets) == 1:
            primary = self.all_bullets[-1].strip()
            if primary:
                self.primary_bullet = primary
                self.bullet_count = 1
            else:
                self.bullet_count_empty = 1
        elif len(self.all_bullets) > 1:
            self.primary_bullet = self.all_bullets[0].strip()
            for bullet in self.all_bullets[1:]:
                stripped_bullet = bullet.strip()
                if not stripped_bullet:
                    self.bullet_count_empty += 1
                else:
                    self.content_bullets.append(stripped_bullet)
                    self.bullet_count += 1

    def get_bullet_density(self):
        """ "Calculate bullet density: ~Char count / Bullet count"""
        if self.bullet_count:
            self.bullet_density = round(self.char_count / self.bullet_count, 2)
