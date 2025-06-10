"""
Module for LogseqBullets class
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Generator

import logseq_analyzer.patterns.adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.patterns.code as CodePatterns
import logseq_analyzer.patterns.content as ContentPatterns
import logseq_analyzer.patterns.double_curly as DoubleCurlyBracketsPatterns
import logseq_analyzer.patterns.double_parentheses as DoubleParenthesesPatterns
import logseq_analyzer.patterns.embedded_links as EmbeddedLinksPatterns
import logseq_analyzer.patterns.external_links as ExternalLinksPatterns

from ..utils.enums import CritCode, CritContent, CritProp
from ..utils.helpers import (
    extract_builtin_properties,
    iter_pattern_split,
    process_aliases,
    process_pattern_hierarchy,
    remove_builtin_properties,
)
from .info import BulletInfo

logger = logging.getLogger(__name__)

RAW_DATA_MAP = {
    CritCode.INLINE: CodePatterns.INLINE_CODE_BLOCK,
    CritContent.ANY_LINKS: ContentPatterns.ANY_LINK,
    CritContent.ASSETS: ContentPatterns.ASSET,
}

PATTERN_MODULES = (
    AdvancedCommandPatterns,
    CodePatterns,
    DoubleCurlyBracketsPatterns,
    DoubleParenthesesPatterns,
    EmbeddedLinksPatterns,
    ExternalLinksPatterns,
)


@dataclass(slots=True)
class LogseqBullets:
    """LogseqBullets class."""

    content: str
    all_bullets: list[str | None] = field(default_factory=list)
    primary: str = ""

    def process(self, bullet_pattern=ContentPatterns.BULLET) -> None:
        """Process the content to extract bullet information."""
        if not (content := self.content):
            return

        append_all_bullets = self.all_bullets.append

        for bullet_index, bullet in iter_pattern_split(bullet_pattern, content):
            append_all_bullets(bullet)
            if bullet and bullet_index == 0:
                self.primary = bullet

    def get_bullet_info(self) -> BulletInfo:
        """Get bullet statistics."""
        _char_count = len(self.content)
        _b_count = len(self.all_bullets)
        _b_empty = self.all_bullets.count("")
        return BulletInfo(
            chars=_char_count,
            bullets=_b_count,
            empty_bullets=_b_empty,
            char_per_bullet=round(_char_count / _b_count, 2) if _b_count else None,
        )

    def extract_primary_raw_data(self) -> Generator[tuple[str, Any]]:
        """Extract primary data from the content."""
        _content = self.content
        _raw_data_map = RAW_DATA_MAP.items()
        for key, value in _raw_data_map:
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
            CritProp.BLOCK_BUILTIN: extract_builtin_properties(block_props),
            CritProp.BLOCK_USER: remove_builtin_properties(block_props),
            CritProp.PAGE_BUILTIN: extract_builtin_properties(page_props),
            CritProp.PAGE_USER: remove_builtin_properties(page_props),
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
            CritContent.ALIASES: aliases,
            CritProp.VALUES: propvalues,
        }.items():
            if value:
                yield key, value

    def extract_patterns(self) -> Generator[tuple[str, Any]]:
        """
        Process patterns in the content.
        """
        _content = self.content
        temp_map = defaultdict(list)
        for pattern in PATTERN_MODULES:
            for key, value in process_pattern_hierarchy(_content, pattern):
                temp_map[key].append(value)

        if not temp_map:
            return

        for key, values in temp_map.items():
            yield key, values
