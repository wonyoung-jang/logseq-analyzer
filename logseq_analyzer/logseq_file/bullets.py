"""
Module for LogseqBullets class
"""

import logging
from collections import defaultdict
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

    char_count: int
    bullet_count: int
    bullet_count_empty: int
    bullet_density: float


class LogseqBullets:
    """LogseqBullets class."""

    __slots__ = (
        "all_bullets",
        "content",
        "has_page_properties",
        "primary",
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
        self.all_bullets: list[str | None] = []
        self.content: str = content
        self.primary: str = ""
        self.stats: BulletStats = None

    def __repr__(self) -> str:
        """Return a string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a user-friendly string representation of the LogseqBullets object."""
        return f"{self.__class__.__qualname__}"

    def process(self, bullet_pattern=ContentPatterns.BULLET) -> None:
        """Process the content to extract bullet information."""
        _content = self.content
        if not _content:
            return

        append_all_bullets = self.all_bullets.append
        b_count = 0
        b_empty = 0
        primary_bullet = ""

        for bullet_index, bullet in iter_pattern_split(bullet_pattern, _content):
            if bullet:
                append_all_bullets(bullet)
                b_count += 1
                if bullet_index == 0:
                    primary_bullet = bullet
            else:
                b_empty += 1

        self.primary = primary_bullet

        _char_count = len(_content)
        self.stats = BulletStats(
            char_count=_char_count,
            bullet_count=b_count,
            bullet_count_empty=b_empty,
            bullet_density=round(_char_count / b_count, 2) if b_count else 0.0,
        )

    def extract_primary_raw_data(self) -> Generator[tuple[str, Any]]:
        """Extract primary data from the content."""
        _content = self.content
        for key, value in {
            Criteria.COD_INLINE: CodePatterns.INLINE_CODE_BLOCK,
            Criteria.CON_ANY_LINKS: ContentPatterns.ANY_LINK,
            Criteria.CON_ASSETS: ContentPatterns.ASSET,
        }.items():
            if value.search(_content):
                yield key, value.findall(_content)

    def extract_properties(self) -> Generator[tuple[str, Any]]:
        """Extract page and block properties from the content."""
        page_props = set()
        _content = self.content
        _all_bullets = self.all_bullets
        primary_bullet = self.primary
        find_all_properties = ContentPatterns.PROPERTY.findall
        if primary_bullet and not primary_bullet.startswith("#"):
            page_props.update(find_all_properties(primary_bullet))
            _content = "\n".join(_all_bullets)
            self.content = _content
        block_props = set(find_all_properties(_content))
        for key, value in {
            Criteria.PROP_BLOCK_BUILTIN: extract_builtin_properties(block_props),
            Criteria.PROP_BLOCK_USER: remove_builtin_properties(block_props),
            Criteria.PROP_PAGE_BUILTIN: extract_builtin_properties(page_props),
            Criteria.PROP_PAGE_USER: remove_builtin_properties(page_props),
        }.items():
            if value:
                yield key, value

    def extract_aliases_and_propvalues(self) -> Generator[tuple[str, Any]]:
        """Extract aliases and properties from the content."""
        _content = self.content
        propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(_content))
        if aliases := propvalues.get("alias"):
            aliases = list(process_aliases(aliases))
        for key, value in {
            Criteria.CON_ALIASES: aliases,
            Criteria.PROP_VALUES: propvalues,
        }.items():
            if value:
                yield key, value

    def extract_patterns(self) -> Generator[tuple[str, Any]]:
        """
        Process patterns in the content.
        """
        _content = self.content
        temp_map = defaultdict(list)
        for pattern in LogseqBullets._PATTERN_MODULES:
            for key, value in process_pattern_hierarchy(_content, pattern):
                temp_map[key].append(value)

        if not temp_map:
            return

        for key, values in temp_map.items():
            yield key, values
