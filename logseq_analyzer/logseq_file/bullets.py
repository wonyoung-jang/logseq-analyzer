"""
Module for LogseqBullets class
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import logseq_analyzer.utils.patterns_content as ContentPatterns

from ..utils.helpers import iter_pattern_split

logger = logging.getLogger(__name__)


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
        "path",
        "content",
        "primary_bullet",
        "content_bullets",
        "stats",
    )

    def __init__(self, path: Path) -> None:
        """Post-initialization method to set bullet attributes."""
        self.path: Path = path
        self.stats: BulletStats = BulletStats()
        self.content: str = ""
        self.primary_bullet: str = ""
        self.content_bullets: list[str | None] = []

    def __repr__(self) -> str:
        """Return a string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}({self.path})"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}: {self.path}"

    def process(self) -> None:
        """Process the content to extract bullet information."""
        self.get_content()
        self.get_char_count()
        if self.content:
            self.get_primary_bullet()
            self.get_bullet_density()
            self.is_primary_bullet_page_properties()

    def get_content(self) -> None:
        """Read the text content of a file."""
        try:
            self.content = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Failed to decode file %s with utf-8 encoding.", self.path)

    def get_char_count(self) -> None:
        """Get the character count of the content."""
        self.stats.char_count = len(self.content)

    def get_primary_bullet(self) -> None:
        """Get the Logseq primary bullet if available"""
        for count, bullet in iter_pattern_split(ContentPatterns.BULLET, self.content):
            if bullet:
                if count == 0:
                    self.primary_bullet = bullet
                self.content_bullets.append(bullet)
                self.stats.bullet_count += 1
            else:
                self.stats.bullet_count_empty += 1

    def get_bullet_density(self) -> None:
        """Get the bullet density of the content."""
        count = self.stats.bullet_count
        self.stats.bullet_density = round(self.stats.char_count / count, 2) if count else 0.0

    def is_primary_bullet_page_properties(self) -> None:
        """Process primary bullet data."""
        prim = self.primary_bullet
        self.stats.has_page_properties = True if prim and not prim.startswith("#") else False
