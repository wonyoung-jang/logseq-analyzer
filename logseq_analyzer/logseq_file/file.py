"""
LogseqFile class to process Logseq files.
"""

import uuid
from re import Pattern
from pathlib import Path
from typing import Any, Generator

from ..config.builtin_properties import split_builtin_user_properties
from ..utils.enums import Criteria
from ..utils.helpers import process_aliases
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
        self.path = LogseqFilename(file_path)
        self.stat = LogseqFilestats(file_path)
        self.bullets = LogseqBullets(file_path)
        self.data: dict = {}
        self.has_backlinks: bool = False
        self.is_backlinked: bool = False
        self.is_backlinked_by_ns_only: bool = False
        self.node_type: str = "other"
        self.file_type: str = "other"
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
            for attr, value in LogseqFile.collect_attrs(subdata):
                if subdata is self.bullets and attr in _large:
                    continue
                setattr(self, attr, value)

    @staticmethod
    def collect_attrs(obj: object) -> Generator[tuple[str, Any], None, None]:
        """Collect slotted attributes from an object."""
        for slot in getattr(type(obj), "__slots__", ()):
            yield slot, getattr(obj, slot)

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""

        # Mask code blocks to avoid interference with pattern matching
        raw_content = self.bullets.content
        masked_content, masked_blocks = self.mask_blocks(raw_content)
        self.masked_blocks = masked_blocks

        primary_data = LogseqFile._extract_primary_data(masked_content, raw_content)

        # Process aliases and property:values
        properties_values = dict(ContentPatterns.property_value.findall(raw_content))
        if aliases := properties_values.get("alias"):
            aliases = process_aliases(aliases)
        # Process aliases and properties
        page_properties = set()
        if self.bullets.has_page_properties:
            page_properties = set(ContentPatterns.property.findall(self.bullets.primary_bullet))
            raw_content = "\n".join(self.bullets.content_bullets)
        block_properties = set(ContentPatterns.property.findall(raw_content))
        self.bullets.content = raw_content
        # Process families of patterns
        aliases_and_properties = LogseqFile._extract_aliases_and_properties(
            properties_values, aliases, page_properties, block_properties
        )
        primary_data.update(aliases_and_properties)
        primary_data.update(self.find_and_process_pattern(CodePatterns))
        primary_data.update(self.find_and_process_pattern(DoubleParenthesesPatterns))
        primary_data.update(self.find_and_process_pattern(ExternalLinksPatterns))
        primary_data.update(self.find_and_process_pattern(EmbeddedLinksPatterns))
        primary_data.update(self.find_and_process_pattern(DoubleCurlyBracketsPatterns))
        primary_data.update(self.find_and_process_pattern(AdvancedCommandPatterns))
        self.check_has_backlinks(primary_data)

    @staticmethod
    def _extract_aliases_and_properties(
        properties_values: dict, aliases: list, page_properties: set, block_properties: set
    ) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Args:
            properties_values (dict): Dictionary containing property values.
            aliases (list): List of aliases.
            page_properties (set): Set of page properties.
            block_properties (set): Set of block properties.
        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        page_props = split_builtin_user_properties(page_properties)
        block_props = split_builtin_user_properties(block_properties)
        return {
            Criteria.ALIASES.value: aliases,
            Criteria.PROPERTIES_BLOCK_BUILTIN.value: block_props.get("built_ins", []),
            Criteria.PROPERTIES_BLOCK_USER.value: block_props.get("user_props", []),
            Criteria.PROPERTIES_PAGE_BUILTIN.value: page_props.get("built_ins", []),
            Criteria.PROPERTIES_PAGE_USER.value: page_props.get("user_props", []),
            Criteria.PROPERTIES_VALUES.value: properties_values,
        }

    @staticmethod
    def _extract_primary_data(masked_content: str, raw_content: str) -> dict[str, str]:
        """
        Extract primary data from the content.

        Args:
            masked_content (str): The content to extract data from.
            raw_content (str): The raw content to extract data from.
        Returns:
            dict: A dictionary containing the extracted data.
        """
        return {
            Criteria.INLINE_CODE_BLOCKS.value: CodePatterns.inline_code_block.findall(raw_content),
            Criteria.ASSETS.value: ContentPatterns.asset.findall(raw_content),
            Criteria.ANY_LINKS.value: ContentPatterns.any_link.findall(raw_content),
            Criteria.BLOCKQUOTES.value: ContentPatterns.blockquote.findall(masked_content),
            Criteria.DRAWS.value: ContentPatterns.draw.findall(masked_content),
            Criteria.FLASHCARDS.value: ContentPatterns.flashcard.findall(masked_content),
            Criteria.PAGE_REFERENCES.value: ContentPatterns.page_reference.findall(masked_content),
            Criteria.TAGGED_BACKLINKS.value: ContentPatterns.tagged_backlink.findall(masked_content),
            Criteria.TAGS.value: ContentPatterns.tag.findall(masked_content),
            Criteria.DYNAMIC_VARIABLES.value: ContentPatterns.dynamic_variable.findall(masked_content),
            Criteria.BOLD.value: ContentPatterns.bold.findall(masked_content),
        }

    def check_has_backlinks(self, primary_data: dict[str, str]) -> None:
        """
        Check has backlinks in the content.

        Args:
            primary_data (dict[str, str]): Dictionary containing primary data.
        """
        data = {}
        has_backlinks = self.has_backlinks
        for key, value in primary_data.items():
            if value:
                data[key] = value
            if has_backlinks:
                continue
            if key in ("page_references", "tags", "tagged_backlinks") or "properties" in key:
                has_backlinks = True
        self.data = data
        self.has_backlinks = has_backlinks

    def find_and_process_pattern(self, pattern) -> Any:
        """
        Find and process a specific pattern in the content.

        Args:
            pattern: The pattern to find and process.
        """
        content = self.bullets.content
        all_pattern: Pattern = getattr(pattern, "all", None)
        results = all_pattern.findall(content)
        return pattern.process(results)

    def determine_node_type(self) -> None:
        """Helper function to determine node type based on summary data."""
        self.node_type = {
            (True, True, True, True): "branch",
            (True, True, False, True): "branch",
            (True, False, True, True): "branch",
            (True, True, True, False): "leaf",
            (True, True, False, False): "leaf",
            (False, True, True, False): "leaf",
            (False, True, False, False): "leaf",
            (True, False, False, True): "root",
            (True, False, True, False): "orphan_namespace",
            (False, False, True, False): "orphan_namespace_true",
            (True, False, False, False): "orphan_graph",
            (False, False, False, False): "orphan_true",
        }.get((self.stat.has_content, self.is_backlinked, self.is_backlinked_by_ns_only, self.has_backlinks), "other")

    def mask_blocks(self, content: str) -> tuple[str, dict[str, str]]:
        """
        Mask code blocks and other patterns in the content.

        Args:
            content (str): The content to mask.
        Returns:
            masked_content: the content with placeholders in place of each match
            masked_blocks: a dict mapping each placeholder to the original text
        """
        patterns = [
            (CodePatterns.all, "__CODE_BLOCK_"),
            (CodePatterns.inline_code_block, "__INLINE_CODE_"),
            (AdvancedCommandPatterns.all, "__ADV_COMMAND_"),
            (DoubleCurlyBracketsPatterns.all, "__DBLCURLY_"),
            (EmbeddedLinksPatterns.all, "__EMB_LINK_"),
            (ExternalLinksPatterns.all, "__EXT_LINK_"),
            (DoubleParenthesesPatterns.all, "__DBLPAREN_"),
            (ContentPatterns.any_link, "__ANY_LINK_"),
        ]

        masked_blocks: dict[str, str] = {}
        masked_content = content

        for regex, prefix in patterns:

            def _repl(match) -> str:
                placeholder = f"{prefix}{uuid.uuid4()}__"
                masked_blocks[placeholder] = match.group(0)
                return placeholder

            masked_content = regex.sub(_repl, masked_content)

        return masked_content, masked_blocks

    def unmask_blocks(self, masked_content: str, masked_blocks: dict[str, str]) -> str:
        """
        Restore the original content by replacing placeholders with their blocks.

        Args:
            masked_content (str): Content with code block placeholders.
            masked_blocks (dict[str, str]): Mapping of placeholders to original code blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        content = masked_content
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
