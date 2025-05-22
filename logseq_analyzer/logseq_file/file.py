"""
LogseqFile class to process Logseq files.
"""

import uuid
from pathlib import Path
from typing import Any

from ..config.builtin_properties import get_builtin_properties, get_not_builtin_properties
from ..utils.enums import Criteria, Nodes, FileTypes
from ..utils.helpers import process_aliases, yield_attrs
from ..utils.patterns import (
    AdvancedCommandPatterns,
    CodePatterns,
    ContentPatterns,
    DoubleCurlyBracketsPatterns,
    DoubleParenthesesPatterns,
    EmbeddedLinksPatterns,
    ExternalLinksPatterns,
)
from .bullets import LogseqBullets
from .name import LogseqFilename
from .stats import LogseqFilestats


class LogseqFile:
    """A class to represent a Logseq file."""

    def __init__(self, file_path: Path) -> None:
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.file_path: Path = file_path
        self.path: LogseqFilename = LogseqFilename(file_path)
        self.stat: LogseqFilestats = LogseqFilestats(file_path)
        self.bullets: LogseqBullets = LogseqBullets(file_path)
        self.data: dict[str, Any] = {}
        self.has_backlinks: bool = False
        self.is_backlinked: bool = False
        self.is_backlinked_by_ns_only: bool = False
        self.node_type: str = Nodes.OTHER.value
        self.file_type: str = FileTypes.OTHER.value
        self.masked_content: str = ""
        self.masked_blocks: dict[str, str] = {}

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}(file_path="{self.file_path}")'

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.file_path}"

    def __hash__(self) -> int:
        return hash(self.path.parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.parts == other.path.parts
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.name < other.path.name
        if isinstance(other, str):
            return self.path.name < other
        return NotImplemented

    def init_file_data(self) -> None:
        """Extract metadata from a file."""
        self.path.process_filename()
        self.stat.process_stats()
        self.bullets.process_bullets()
        self._set_file_data_attributes()

    def _set_file_data_attributes(self) -> None:
        """Set file data attributes."""
        _large = ("all_bullets", "content_bullets", "content")
        for subdata in (self.stat, self.path, self.bullets):
            for attr, value in yield_attrs(subdata):
                if subdata is self.bullets and attr in _large:
                    continue
                setattr(self, attr, value)

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        self.mask_blocks()
        primary_data = {}
        primary_data.update(self.extract_primary_data())
        primary_data.update(self.extract_aliases_and_propvalues())
        primary_data.update(self.extract_properties())
        primary_data.update(self.extract_patterns())
        self.check_has_backlinks(primary_data)

    def mask_blocks(self) -> None:
        """
        Mask code blocks and other patterns in the content.
        """
        patterns = (
            (CodePatterns.all, "__CODE_BLOCK_"),
            (CodePatterns.inline_code_block, "__INLINE_CODE_"),
            (AdvancedCommandPatterns.all, "__ADV_COMMAND_"),
            (DoubleCurlyBracketsPatterns.all, "__DBLCURLY_"),
            (EmbeddedLinksPatterns.all, "__EMB_LINK_"),
            (ExternalLinksPatterns.all, "__EXT_LINK_"),
            (DoubleParenthesesPatterns.all, "__DBLPAREN_"),
            (ContentPatterns.any_link, "__ANY_LINK_"),
        )

        masked_blocks: dict[str, str] = {}
        masked_content = self.bullets.content

        for regex, prefix in patterns:

            def _repl(match, prefix=prefix) -> str:
                placeholder = f"{prefix}{uuid.uuid4()}__"
                masked_blocks[placeholder] = match.group(0)
                return placeholder

            masked_content = regex.sub(_repl, masked_content)

        self.masked_blocks = masked_blocks
        self.masked_content = masked_content

    def extract_primary_data(self) -> dict[str, str]:
        """
        Extract primary data from the content.

        Returns:
            dict: A dictionary containing the extracted data.
        """
        content = self.bullets.content
        masked_content = self.masked_content
        return {
            Criteria.INLINE_CODE_BLOCKS.value: CodePatterns.inline_code_block.findall(content),
            Criteria.ASSETS.value: ContentPatterns.asset.findall(content),
            Criteria.ANY_LINKS.value: ContentPatterns.any_link.findall(content),
            Criteria.BLOCKQUOTES.value: ContentPatterns.blockquote.findall(masked_content),
            Criteria.DRAWS.value: ContentPatterns.draw.findall(masked_content),
            Criteria.FLASHCARDS.value: ContentPatterns.flashcard.findall(masked_content),
            Criteria.PAGE_REFERENCES.value: ContentPatterns.page_reference.findall(masked_content),
            Criteria.TAGGED_BACKLINKS.value: ContentPatterns.tagged_backlink.findall(masked_content),
            Criteria.TAGS.value: ContentPatterns.tag.findall(masked_content),
            Criteria.DYNAMIC_VARIABLES.value: ContentPatterns.dynamic_variable.findall(masked_content),
            Criteria.BOLD.value: ContentPatterns.bold.findall(masked_content),
        }

    def extract_aliases_and_propvalues(self) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        content = self.bullets.content
        properties_values = dict(ContentPatterns.property_value.findall(content))
        if aliases := properties_values.get("alias"):
            aliases = process_aliases(aliases)
        return {
            Criteria.ALIASES.value: aliases,
            Criteria.PROPERTIES_VALUES.value: properties_values,
        }

    def extract_properties(self) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        content = self.bullets.content
        page_properties = set()
        if self.bullets.has_page_properties:
            page_properties = set(ContentPatterns.property.findall(self.bullets.primary_bullet))
            content = "\n".join(self.bullets.content_bullets)
        block_properties = set(ContentPatterns.property.findall(content))
        self.bullets.content = content
        page_props_builtins = sorted(get_builtin_properties(page_properties))
        page_props_user = sorted(get_not_builtin_properties(page_properties))
        block_props_builtins = sorted(get_builtin_properties(block_properties))
        block_props_user = sorted(get_not_builtin_properties(block_properties))
        return {
            Criteria.PROPERTIES_BLOCK_BUILTIN.value: block_props_builtins,
            Criteria.PROPERTIES_BLOCK_USER.value: block_props_user,
            Criteria.PROPERTIES_PAGE_BUILTIN.value: page_props_builtins,
            Criteria.PROPERTIES_PAGE_USER.value: page_props_user,
        }

    def extract_patterns(self) -> dict[str, Any]:
        """
        Process patterns in the content.

        Returns:
            dict: A dictionary containing the processed patterns.
        """
        patterns = (
            CodePatterns,
            DoubleParenthesesPatterns,
            ExternalLinksPatterns,
            EmbeddedLinksPatterns,
            DoubleCurlyBracketsPatterns,
            AdvancedCommandPatterns,
        )
        result = {}
        content = self.bullets.content
        for pattern in patterns:
            all_pattern = pattern.all.finditer(content)
            result.update(pattern.process(all_pattern))
        return result

    def check_has_backlinks(self, primary_data: dict[str, str]) -> None:
        """
        Check has backlinks in the content.

        Args:
            primary_data (dict[str, str]): Dictionary containing primary data.
        """
        data = {}
        has_backlinks = self.has_backlinks
        backlinks = (
            Criteria.PAGE_REFERENCES.value,
            Criteria.TAGGED_BACKLINKS.value,
            Criteria.TAGS.value,
        )
        for key, value in primary_data.items():
            if value:
                data[key] = value
            if has_backlinks:
                continue
            if key in backlinks or "properties" in key:
                has_backlinks = True
        self.data = data
        self.has_backlinks = has_backlinks

    def determine_node_type(self) -> None:
        """Helper function to determine node type based on summary data."""
        self.node_type = {
            (True, True, True, True): Nodes.BRANCH.value,
            (True, True, False, True): Nodes.BRANCH.value,
            (True, False, True, True): Nodes.BRANCH.value,
            (True, True, True, False): Nodes.LEAF.value,
            (True, True, False, False): Nodes.LEAF.value,
            (False, True, True, False): Nodes.LEAF.value,
            (False, True, False, False): Nodes.LEAF.value,
            (True, False, False, True): Nodes.ROOT.value,
            (True, False, True, False): Nodes.ORPHAN_NAMESPACE.value,
            (False, False, True, False): Nodes.ORPHAN_NAMESPACE_TRUE.value,
            (True, False, False, False): Nodes.ORPHAN_GRAPH.value,
            (False, False, False, False): Nodes.ORPHAN_TRUE.value,
        }.get(
            (self.stat.has_content, self.is_backlinked, self.is_backlinked_by_ns_only, self.has_backlinks),
            Nodes.OTHER.value,
        )

    def unmask_blocks(self) -> str:
        """
        Restore the original content by replacing placeholders with their blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        content = self.masked_content
        masked_blocks = self.masked_blocks
        for placeholder, block in masked_blocks.items():
            content = content.replace(placeholder, block)
        return content

    def check_is_backlinked(self, lookup: set[str]) -> bool:
        """
        Helper function to check if a file is backlinked.

        Args:
            lookup (set[str]): Set of backlinks to check against.

        Returns:
            bool: True if the file is backlinked, False otherwise.
        """
        try:
            lookup.remove(self.path.name)
            return True
        except KeyError:
            return False
