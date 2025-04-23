"""
Module for LogseqBullets class
"""

from dataclasses import dataclass, field
from pathlib import Path
import logging

from ..utils.patterns import ContentPatterns


@dataclass
class LogseqBullets:
    """LogseqBullets class"""

    file_path: Path

    content: str = ""
    primary_bullet: str = ""
    all_bullets: list = field(default_factory=list)
    content_bullets: list = field(default_factory=list)
    char_count: int = 0
    bullet_count: int = 0
    bullet_count_empty: int = 0
    bullet_density: float = 0.0
    has_page_properties: bool = False

    def __post_init__(self):
        """Initialize the LogseqBullets class"""
        self.get_content()
        self.get_char_count()
        self.get_bullet_content()
        self.get_primary_bullet()
        self.get_bullet_density()
        self.is_primary_bullet_page_properties()

    def __repr__(self):
        return f'LogseqBullets(file_path="{self.file_path}")'

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
            self.all_bullets = ContentPatterns().bullet.split(self.content)

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
        """Calculate bullet density: ~Char count / Bullet count"""
        if self.bullet_count:
            self.bullet_density = round(self.char_count / self.bullet_count, 2)

    def is_primary_bullet_page_properties(self):
        """Process primary bullet data."""
        bullet = self.primary_bullet.strip()
        if bullet and not bullet.startswith("#"):
            self.has_page_properties = True
