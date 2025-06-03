"""
Module for LogseqBullets class
"""

import logging
from dataclasses import dataclass
from typing import Any, Generator

import logseq_analyzer.patterns.adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.patterns.code as CodePatterns
import logseq_analyzer.patterns.content as ContentPatterns
import logseq_analyzer.patterns.double_curly as DoubleCurlyBracketsPatterns
import logseq_analyzer.patterns.double_parentheses as DoubleParenthesesPatterns
import logseq_analyzer.patterns.embedded_links as EmbeddedLinksPatterns
import logseq_analyzer.patterns.external_links as ExternalLinksPatterns

from ..utils.enums import Criteria
from ..utils.helpers import (
    extract_builtin_properties,
    iter_pattern_split,
    process_aliases,
    process_pattern_hierarchy,
    remove_builtin_properties,
)

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

    _PATTERN_MODULES = (
        AdvancedCommandPatterns,
        CodePatterns,
        DoubleCurlyBracketsPatterns,
        DoubleParenthesesPatterns,
        EmbeddedLinksPatterns,
        ExternalLinksPatterns,
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
        _bullet_count = self.stats.bullet_count
        _char_count = self.stats.char_count

        if _bullet_count:
            return round(_char_count / _bullet_count, 2)
        return 0.0

    def process(self) -> None:
        """Process the content to extract bullet information."""
        _content = self.content
        if not _content:
            return

        _all_bullets = self.all
        bullet_count = 0
        bullet_count_empty = 0
        primary_bullet = ""

        for bullet_index, bullet in iter_pattern_split(ContentPatterns.BULLET, _content):
            if bullet:
                _all_bullets.append(bullet)
                bullet_count += 1
                if bullet_index == 0:
                    primary_bullet = bullet
            else:
                bullet_count_empty += 1

        self.stats.char_count = len(_content)
        self.stats.bullet_count = bullet_count
        self.stats.bullet_count_empty = bullet_count_empty
        self.primary = primary_bullet

    def extract_primary_raw_data(self) -> Generator[tuple[str, Any]]:
        """Extract primary data from the content."""
        _content = self.content
        result = {
            Criteria.COD_INLINE.value: CodePatterns.INLINE_CODE_BLOCK.findall(_content),
            Criteria.CON_ANY_LINKS.value: ContentPatterns.ANY_LINK.findall(_content),
            Criteria.CON_ASSETS.value: ContentPatterns.ASSET.findall(_content),
        }
        for key, value in {k: v for k, v in result.items() if v}.items():
            yield (key, value)

    def extract_properties(self) -> Generator[tuple[str, Any]]:
        """Extract page and block properties from the content."""
        page_props = set()
        _content = self.content
        _primary_bullet = self.primary
        _all_bullets = self.all
        _find_all_properties = ContentPatterns.PROPERTY.findall

        if self.has_page_properties:
            page_props.update(_find_all_properties(_primary_bullet))
            _content = "\n".join(_all_bullets)
            self.content = _content
        block_props = set(_find_all_properties(_content))
        result = {
            Criteria.PROP_BLOCK_BUILTIN.value: extract_builtin_properties(block_props),
            Criteria.PROP_BLOCK_USER.value: remove_builtin_properties(block_props),
            Criteria.PROP_PAGE_BUILTIN.value: extract_builtin_properties(page_props),
            Criteria.PROP_PAGE_USER.value: remove_builtin_properties(page_props),
        }
        for key, value in {k: v for k, v in result.items() if v}.items():
            yield (key, value)

    def extract_aliases_and_propvalues(self) -> Generator[tuple[str, Any]]:
        """Extract aliases and properties from the content."""
        _content = self.content
        propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(_content))
        if aliases := propvalues.get("alias"):
            aliases = list(process_aliases(aliases))
        result = {
            Criteria.CON_ALIASES.value: aliases,
            Criteria.PROP_VALUES.value: propvalues,
        }
        for key, value in {k: v for k, v in result.items() if v}.items():
            yield (key, value)

    def extract_patterns(self) -> Generator[tuple[str, Any]]:
        """
        Process patterns in the content.
        """
        _content = self.content
        _pattern_modules = LogseqBullets._PATTERN_MODULES

        result = {}
        for pattern in _pattern_modules:
            processed_patterns = process_pattern_hierarchy(_content, pattern)
            result.update(processed_patterns)
        for key, value in {k: v for k, v in result.items() if v}.items():
            yield (key, value)
