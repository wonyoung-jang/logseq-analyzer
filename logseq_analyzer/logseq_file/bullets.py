"""
Module for LogseqBullets class
"""

import logging
from dataclasses import dataclass

import logseq_analyzer.utils.patterns_content as ContentPatterns

from ..utils.helpers import iter_pattern_split

logger = logging.getLogger(__name__)


@dataclass
class BulletStats:
    """Bullet statistics class."""

    char_count: int = 0
    bullet_count: int = 0
    bullet_count_empty: int = 0


class LogseqBullets:
    """LogseqBullets class."""

    __slots__ = (
        "content",
        "primary",
        "all",
        "stats",
    )

    def __init__(self, content: str = "") -> None:
        """Post-initialization method to set bullet attributes."""
        self.content: str = content
        self.primary: str = ""
        self.all: list[str | None] = []
        self.stats: BulletStats = BulletStats()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}"

    @property
    def has_page_properties(self) -> bool:
        """Check if the primary bullet has page properties."""
        return self.primary and not self.primary.startswith("#")

    @property
    def bullet_density(self) -> float:
        """Get the bullet density of the content."""
        if self.stats.bullet_count:
            return round(self.stats.char_count / self.stats.bullet_count, 2)
        return 0.0

    def process(self) -> None:
        """Process the content to extract bullet information."""
        if not self.content:
            return
        for count, bullet in iter_pattern_split(ContentPatterns.BULLET, self.content):
            if bullet:
                self.all.append(bullet)
                self.stats.bullet_count += 1
                if count == 0:
                    self.primary = bullet
            else:
                self.stats.bullet_count_empty += 1
