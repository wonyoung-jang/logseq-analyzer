"""
Module for LogseqBullets class
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import logseq_analyzer.utils.patterns_content as ContentPatterns


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
        "all_bullets",
        "content_bullets",
        "stats",
    )

    def __init__(self, file_path: Path) -> None:
        """Post-initialization method to set bullet attributes."""
        self.file_path: Path = file_path
        self.stats: BulletStats = BulletStats()
        self.content: str = ""
        self.primary_bullet: str = ""
        self.all_bullets: list[str | None] = []
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
            self.stats.char_count = len(self.content)
            self.all_bullets = ContentPatterns.BULLET.split(self.content)
            self.get_primary_bullet()
            self.is_primary_bullet_page_properties()
            if self.stats.bullet_count:
                self.stats.bullet_density = round(self.stats.char_count / self.stats.bullet_count, 2)

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
        content_bullets = self.content_bullets
        bullet_count = 0
        bullet_count_empty = 0
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
        self.stats.bullet_count = bullet_count
        self.stats.bullet_count_empty = bullet_count_empty
        self.primary_bullet = primary_bullet

    def is_primary_bullet_page_properties(self) -> None:
        """Process primary bullet data."""
        bullet = self.primary_bullet.strip()
        if bullet and not bullet.startswith("#"):
            self.stats.has_page_properties = True
