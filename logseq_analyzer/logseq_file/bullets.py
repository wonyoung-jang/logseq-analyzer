"""
Module for LogseqBullets class
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from ..utils.patterns import ContentPatterns


@dataclass
class LogseqBullets:
    """
    LogseqBullets class.
    """

    file_path: Path
    content: str = field(init=False, repr=False)
    primary_bullet: str = field(init=False, repr=False)
    all_bullets: list[str] = field(init=False, repr=False)
    content_bullets: list[str] = field(init=False, repr=False)
    char_count: int = field(init=False, repr=False)
    bullet_count: int = field(init=False, repr=False)
    bullet_count_empty: int = field(init=False, repr=False)
    bullet_density: float = field(init=False, repr=False)
    has_page_properties: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Post-initialization method to set bullet attributes."""
        self.content = ""
        self.primary_bullet = ""
        self.all_bullets = []
        self.content_bullets = []
        self.char_count = 0
        self.bullet_count = 0
        self.bullet_count_empty = 0
        self.bullet_density = 0.0
        self.has_page_properties = False

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
        primary = ""
        all_bullets = self.all_bullets
        bullet_count = 0
        bullet_count_empty = 0
        content_bullets = []
        if len(all_bullets) == 1:
            if primary := all_bullets[0].strip():
                bullet_count = 1
            else:
                bullet_count_empty = 1
        elif len(all_bullets) > 1:
            primary = all_bullets[0].strip()
            for bullet in all_bullets[1:]:
                if not (stripped_bullet := bullet.strip()):
                    bullet_count_empty += 1
                else:
                    content_bullets.append(stripped_bullet)
                    bullet_count += 1
        self.bullet_count = bullet_count
        self.bullet_count_empty = bullet_count_empty
        self.content_bullets = content_bullets
        self.primary_bullet = primary

    def get_bullet_density(self) -> None:
        """Calculate bullet density: ~Char count / Bullet count"""
        if self.bullet_count:
            self.bullet_density = round(self.char_count / self.bullet_count, 2)

    def is_primary_bullet_page_properties(self) -> None:
        """Process primary bullet data."""
        bullet = self.primary_bullet.strip()
        if bullet and not bullet.startswith("#"):
            self.has_page_properties = True
