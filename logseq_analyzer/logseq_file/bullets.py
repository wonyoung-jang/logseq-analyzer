"""Module for LogseqBullets class."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.logseq_file.info import BulletInfo
from logseq_analyzer.patterns.content import ContentPatterns
from logseq_analyzer.patterns.patterns import PATTERNS
from logseq_analyzer.utils.enums import CritCode, CritContent, CritProp
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES

if TYPE_CHECKING:
    from collections.abc import Iterator


logger = logging.getLogger(__name__)

RAW_DATA_MAP = {
    CritCode.INLINE: ContentPatterns.INLINE_CODE_BLOCK,
    CritContent.ANY_LINKS: ContentPatterns.ANY_LINK,
    CritContent.ASSETS: ContentPatterns.ASSET,
}


def process_aliases(aliases: str) -> Iterator[str]:
    """Process aliases to extract individual aliases."""
    if not (aliases := aliases.strip()):
        return
    current = []
    is_inside_brackets = False
    pos = 0
    while pos < len(aliases):
        if aliases[pos : pos + 2] == "[[":
            is_inside_brackets = True
            pos += 2
        elif aliases[pos : pos + 2] == "]]":
            is_inside_brackets = False
            pos += 2
        elif aliases[pos] == "," and not is_inside_brackets:
            if part := "".join(current).strip().lower():
                yield part
            current.clear()
            pos += 1
        else:
            current.append(aliases[pos])
            pos += 1
    if part := "".join(current).strip().lower():
        yield part


@dataclass(slots=True)
class LogseqBullets:
    """LogseqBullets class."""

    content: str
    all_bullets: list[str] = field(default_factory=list)
    primary: str = ""

    def __post_init__(self) -> None:
        """Process the content to extract bullet information."""
        if not self.content:
            return
        for bullet_index, bullet in self._iter_pattern_split():
            self.all_bullets.append(bullet)
            if bullet and bullet_index == 0:
                self.primary = bullet

    def _iter_pattern_split(self, maxsplit: int = 0) -> Iterator[tuple[int, str]]:
        """Emulate re.Pattern.split() but yields sections of text instead of returning a list.

        Iterate over sections of text separated by bullet markers.

        Args:
            maxsplit (int): Maximum number of splits. If 0, all sections are returned.

        Yields:
            Iterator[tuple[int, str]]: Sections of text with their respective indices.

        """
        _count = 0
        for match in ContentPatterns.BULLET.finditer(self.content):
            if maxsplit and _count >= maxsplit:
                break
            if _count == 0:
                yield _count, self.content[: match.start()].strip("\t \n")
                _count += 1
            content_start = match.end()
            next_match = next(ContentPatterns.BULLET.finditer(self.content, content_start), None)
            content_end = next_match.start() if next_match else len(self.content)
            yield _count, self.content[content_start:content_end].strip("\t \n")
            _count += 1
        if _count == 0:
            yield _count, self.content.strip("\t \n")

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
            page_props.update(ContentPatterns.PROPERTY.findall(self.primary))
            self.content = "\n".join(self.all_bullets)
        block_props = set(ContentPatterns.PROPERTY.findall(self.content))
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
        propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(self.content))
        if aliases := propvalues.get("alias"):
            aliases = list(process_aliases(aliases))
        for key, value in {
            CritContent.ALIASES: aliases,
            CritProp.VALUES: propvalues,
        }.items():
            if value:
                yield key, value

    def extract_patterns(self) -> Iterator[tuple[str, list[str]]]:
        """Process patterns in the content."""
        _temp_map = defaultdict(list)
        for ptn_cls in PATTERNS:
            for k, v in ptn_cls.process_pattern_hierarchy(self.content):
                _temp_map[k].append(v)
        yield from _temp_map.items()
