"""
Module for LogseqBullets class
"""

from dataclasses import dataclass, field
from pathlib import Path
import logging
from typing import List

from ..utils.patterns import ContentPatterns


@dataclass
class LogseqBullets:
    """LogseqBullets class"""

    file_path: Path

    content: str = ""
    primary_bullet: str = ""
    all_bullets: List[str] = field(default_factory=list)
    content_bullets: List[str] = field(default_factory=list)
    char_count: int = 0
    bullet_count: int = 0
    bullet_count_empty: int = 0
    bullet_density: float = 0.0
    has_page_properties: bool = False

    def get_content(self) -> str:
        """Read the text content of a file."""
        try:
            return self.file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logging.warning("Failed to decode file %s with utf-8 encoding.", self.file_path)
            return ""

    def get_char_count(self) -> int:
        """Get character count of content"""
        return len(self.content)

    def get_bullet_content(self) -> List[str]:
        """Get all bullets split into a list"""
        if not self.content:
            return []
        content_patterns = ContentPatterns()
        return content_patterns.bullet.split(self.content)

    def get_primary_bullet(self) -> str:
        """Get the Logseq primary bullet if available"""
        primary = ""
        if len(self.all_bullets) == 1:
            if primary := self.all_bullets[-1].strip():
                self.bullet_count = 1
            else:
                self.bullet_count_empty = 1
        elif len(self.all_bullets) > 1:
            primary = self.all_bullets[0].strip()
            for bullet in self.all_bullets[1:]:
                if not (stripped_bullet := bullet.strip()):
                    self.bullet_count_empty += 1
                else:
                    self.content_bullets.append(stripped_bullet)
                    self.bullet_count += 1
        return primary

    def get_bullet_density(self) -> float:
        """Calculate bullet density: ~Char count / Bullet count"""
        if not self.bullet_count:
            return 0.0
        return round(self.char_count / self.bullet_count, 2)

    def is_primary_bullet_page_properties(self) -> bool:
        """Process primary bullet data."""
        bullet = self.primary_bullet.strip()
        if bullet and not bullet.startswith("#"):
            return True
        return False
