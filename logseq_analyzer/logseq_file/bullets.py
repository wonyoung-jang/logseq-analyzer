"""
Module for LogseqBullets class
"""

import logging
from pathlib import Path

from ..utils.patterns import ContentPatterns


class LogseqBullets:
    """LogseqBullets class."""

    __slots__ = (
        "file_path",
        "content",
        "primary_bullet",
        "all_bullets",
        "content_bullets",
        "char_count",
        "bullet_count",
        "bullet_count_empty",
        "bullet_density",
        "has_page_properties",
    )

    def __init__(self, file_path: Path) -> None:
        """Post-initialization method to set bullet attributes."""
        self.file_path: Path = file_path
        self.content: str = ""
        self.primary_bullet: str = ""
        self.all_bullets: list[str | None] = []
        self.content_bullets: list[str | None] = []
        self.char_count: int = 0
        self.bullet_count: int = 0
        self.bullet_count_empty: int = 0
        self.bullet_density: float = 0.0
        self.has_page_properties: bool = False

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
            self.char_count = len(self.content)
            self.all_bullets = ContentPatterns.bullet.split(self.content)
            self.get_primary_bullet()
            self.is_primary_bullet_page_properties()
            if self.bullet_count:
                self.bullet_density = round(self.char_count / self.bullet_count, 2)

    def get_content(self) -> None:
        """Read the text content of a file."""
        try:
            self.content = self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logging.warning("Failed to decode file %s with utf-8 encoding.", self.file_path)

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

    def is_primary_bullet_page_properties(self) -> None:
        """Process primary bullet data."""
        bullet = self.primary_bullet.strip()
        if bullet and not bullet.startswith("#"):
            self.has_page_properties = True
