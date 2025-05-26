"""
Module for LogseqBullets class
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import logseq_analyzer.utils.patterns_content as ContentPatterns
from ..utils.helpers import iter_pattern_split


@dataclass
class BulletStats:
    """Bullet statistics class."""

    char_count: int = 0
    bullet_count: int = 0
    bullet_count_empty: int = 0
    bullet_density: float = 0.0
    has_page_properties: bool = False


class LogseqBullets:
    """LogseqBullets class."""

    __slots__ = (
        "file_path",
        "content",
        "primary_bullet",
        "content_bullets",
        "stats",
    )

    def __init__(self, file_path: Path) -> None:
        """Post-initialization method to set bullet attributes."""
        self.file_path: Path = file_path
        self.stats: BulletStats = BulletStats()
        self.content: str = ""
        self.primary_bullet: str = ""
        self.content_bullets: list[str | None] = []

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
        """Get the character count of the content."""
        self.stats.char_count = len(self.content)

    def get_primary_bullet(self) -> None:
        """Get the Logseq primary bullet if available"""
        content_bullets = self.content_bullets
        bullet_count = 0
        bullet_count_empty = 0
        for count, bullet in iter_pattern_split(ContentPatterns.BULLET, self.content):
            if bullet:
                if count == 0:
                    self.primary_bullet = bullet
                content_bullets.append(bullet)
                bullet_count += 1
            else:
                bullet_count_empty += 1
        self.stats.bullet_count = bullet_count
        self.stats.bullet_count_empty = bullet_count_empty

    def get_bullet_density(self) -> None:
        """Get the bullet density of the content."""
        if self.stats.bullet_count:
            self.stats.bullet_density = round(self.stats.char_count / self.stats.bullet_count, 2)

    def is_primary_bullet_page_properties(self) -> None:
        """Process primary bullet data."""
        if self.primary_bullet and not self.primary_bullet.startswith("#"):
            self.stats.has_page_properties = True
