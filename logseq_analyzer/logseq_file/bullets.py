"""Module for LogseqBullets class."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import logseq_analyzer.patterns.adv_cmd as adv_cmd_ptns
import logseq_analyzer.patterns.code as cde_ptns
import logseq_analyzer.patterns.content as content_patterns
import logseq_analyzer.patterns.double_curly as dbl_crly_br_ptns
import logseq_analyzer.patterns.double_parentheses as dbl_prn_ptns
import logseq_analyzer.patterns.embedded_links as emb_lnk_ptns
import logseq_analyzer.patterns.external_links as ext_lnk_ptns
from logseq_analyzer.logseq_file.info import BulletInfo
from logseq_analyzer.utils.enums import CritCode, CritContent, CritProp
from logseq_analyzer.utils.helpers import (
    BUILT_IN_PROPERTIES,
    iter_pattern_split,
    process_aliases,
    process_pattern_hierarchy,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

RAW_DATA_MAP = {
    CritCode.INLINE: cde_ptns.INLINE_CODE_BLOCK,
    CritContent.ANY_LINKS: content_patterns.ANY_LINK,
    CritContent.ASSETS: content_patterns.ASSET,
}
PATTERN_MODULES = (
    (adv_cmd_ptns.ALL, adv_cmd_ptns.PATTERN_MAP, adv_cmd_ptns.FALLBACK),
    (cde_ptns.ALL, cde_ptns.PATTERN_MAP, cde_ptns.FALLBACK),
    (dbl_crly_br_ptns.ALL, dbl_crly_br_ptns.PATTERN_MAP, dbl_crly_br_ptns.FALLBACK),
    (dbl_prn_ptns.ALL, dbl_prn_ptns.PATTERN_MAP, dbl_prn_ptns.FALLBACK),
    (emb_lnk_ptns.ALL, emb_lnk_ptns.PATTERN_MAP, emb_lnk_ptns.FALLBACK),
    (ext_lnk_ptns.ALL, ext_lnk_ptns.PATTERN_MAP, ext_lnk_ptns.FALLBACK),
)


@dataclass(slots=True)
class LogseqBullets:
    """LogseqBullets class."""

    content: str
    all_bullets: list[str] = field(default_factory=list)
    primary: str = ""

    def process(self) -> None:
        """Process the content to extract bullet information."""
        if not (content := self.content):
            return
        for bullet_index, bullet in iter_pattern_split(content_patterns.BULLET, content):
            self.all_bullets.append(bullet)
            if bullet and bullet_index == 0:
                self.primary = bullet

    def get_bullet_info(self) -> BulletInfo:
        """Get bullet statistics."""
        return BulletInfo(
            chars=len(self.content),
            bullets=len(self.all_bullets),
            empty_bullets=self.all_bullets.count(""),
        )

    def extract_primary_raw_data(self) -> Iterator[tuple[str, Any]]:
        """Extract primary data from the content."""
        for key, value in RAW_DATA_MAP.items():
            if value.search(self.content):
                yield key, value.findall(self.content)

    def extract_properties(self) -> Iterator[tuple[str, Any]]:
        """Extract page and block properties from the content."""
        page_props = set()
        if self.primary and not self.primary.startswith("#"):
            page_props.update(content_patterns.PROPERTY.findall(self.primary))
            self.content = "\n".join(self.all_bullets)
        block_props = set(content_patterns.PROPERTY.findall(self.content))
        for key, value in {
            CritProp.BLOCK_BUILTIN: block_props.intersection(BUILT_IN_PROPERTIES),
            CritProp.BLOCK_USER: block_props.difference(BUILT_IN_PROPERTIES),
            CritProp.PAGE_BUILTIN: page_props.intersection(BUILT_IN_PROPERTIES),
            CritProp.PAGE_USER: page_props.difference(BUILT_IN_PROPERTIES),
        }.items():
            if value:
                yield key, value

    def extract_aliases_and_propvalues(self) -> Iterator[tuple[str, Any]]:
        """Extract aliases and properties from the content."""
        propvalues = dict(content_patterns.PROPERTY_VALUE.findall(self.content))
        if aliases := propvalues.get("alias"):
            aliases = list(process_aliases(aliases))
        for key, value in {
            CritContent.ALIASES: aliases,
            CritProp.VALUES: propvalues,
        }.items():
            if value:
                yield key, value

    def extract_patterns(self) -> Iterator[tuple[str, Any]]:
        """Process patterns in the content."""
        _temp_map = defaultdict(list)
        for all_pattern, pattern_map, fallback in PATTERN_MODULES:
            for key, value in process_pattern_hierarchy(self.content, all_pattern, pattern_map, fallback):
                _temp_map[key].append(value)
        if not _temp_map:
            return
        for key, values in _temp_map.items():
            yield key, values
