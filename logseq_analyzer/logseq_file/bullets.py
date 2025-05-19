"""
Module for LogseqBullets class
"""

import logging
from pathlib import Path

from ..utils.patterns import ContentPatterns


class LogseqBullets:
    """LogseqBullets class."""

    def __init__(self, file_path: Path) -> None:
        """Post-initialization method to set bullet attributes."""
        self.file_path = file_path
        self.content = ""
        self.primary_bullet = ""
        self.all_bullets = []
        self.content_bullets = []
        self.char_count = 0
        self.bullet_count = 0
        self.bullet_count_empty = 0
        self.bullet_density = 0.0
        self.has_page_properties = False

    def __repr__(self) -> str:
        """Return a string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}({self.file_path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}: {self.file_path}"

    def process_bullets(self) -> None:
        """Process the content to extract bullet information."""
        self.get_content()
        if self.content:
            self.get_char_count()
            self.get_bullet_content()
            self.get_primary_bullet()
            self.get_bullet_density()
            self.is_primary_bullet_page_properties()

    def get_content(self) -> None:
        """Read the text content of a file."""
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logging.warning("Failed to decode file %s with utf-8 encoding.", self.file_path)

    def get_char_count(self) -> None:
        """Get character count of content"""
        self.char_count = len(self.content)

    def get_bullet_content(self) -> None:
        """Get all bullets split into a list"""
        if self.content:
            self.all_bullets = ContentPatterns.bullet.split(self.content)

    def get_primary_bullet(self) -> None:
        """Get the Logseq primary bullet if available"""
        primary_bullet = ""
        all_bullets = self.all_bullets
        bullet_count = 0
        bullet_count_empty = 0
        content_bullets = []
        if len(all_bullets) == 1:
            if primary_bullet := all_bullets[0].strip():
                bullet_count = 1
            else:
                bullet_count_empty = 1
        elif len(all_bullets) > 1:
            primary_bullet = all_bullets[0].strip()
            for bullet in all_bullets[1:]:
                if not (stripped_bullet := bullet.strip()):
                    bullet_count_empty += 1
                else:
                    content_bullets.append(stripped_bullet)
                    bullet_count += 1
        self.bullet_count = bullet_count
        self.bullet_count_empty = bullet_count_empty
        self.content_bullets = content_bullets
        self.primary_bullet = primary_bullet

    def get_bullet_density(self) -> None:
        """Calculate bullet density: ~Char count / Bullet count"""
        if self.bullet_count:
            self.bullet_density = round(self.char_count / self.bullet_count, 2)

    def is_primary_bullet_page_properties(self) -> None:
        """Process primary bullet data."""
        bullet = self.primary_bullet.strip()
        if bullet and not bullet.startswith("#"):
            self.has_page_properties = True
