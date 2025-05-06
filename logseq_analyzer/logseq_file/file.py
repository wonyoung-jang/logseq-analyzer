"""
LogseqFile class to process Logseq files.
"""

from pathlib import Path
from typing import Dict, Set, Tuple
import uuid

from ..config.builtin_properties import split_builtin_user_properties
from ..utils.enums import Criteria
from ..utils.helpers import find_all_lower, process_aliases
from ..utils.patterns import (
    AdvancedCommandPatterns,
    ContentPatterns,
    DoubleCurlyBracketsPatterns,
    EmbeddedLinksPatterns,
    ExternalLinksPatterns,
    DoubleParenthesesPatterns,
    CodePatterns,
)
from .bullets import LogseqBullets
from .name import LogseqFilename
from .stats import LogseqFilestats


class LogseqFile:
    """A class to represent a Logseq file."""

    def __init__(self, file_path: Path):
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.file_path = file_path
        self.masked_blocks = {}
        self.path = LogseqFilename(file_path)
        self.stat = LogseqFilestats(file_path)
        self.bullets = LogseqBullets(file_path)
        self.content = ""
        self.data = {}
        self.primary_bullet = ""
        self.content_bullets = []
        self.has_content = False
        self.has_backlinks = False
        self.is_backlinked = False
        self.is_backlinked_by_ns_only = False
        self.node_type = "other"
        self.file_type = "other"

    def __repr__(self) -> str:
        return f'LogseqFile(file_path="{self.file_path}")'

    def __str__(self) -> str:
        return f"LogseqFile: {self.file_path}"

    def __hash__(self) -> int:
        return hash(self.path.parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.parts == other.path.parts
        return NotImplemented

    def init_file_data(self):
        """
        Extract metadata from a file.
        """
        self.path.determine_file_type()
        self.path.process_logseq_filename()
        self.path.convert_uri_to_logseq_url()
        self.path.get_namespace_name_data()
        for attr, value in self.path.__dict__.items():
            setattr(self, attr, value)

        for attr, value in self.stat.__dict__.items():
            setattr(self, attr, value)

        self.bullets.get_content()
        self.bullets.get_char_count()
        self.bullets.get_bullet_content()
        self.bullets.get_primary_bullet()
        self.bullets.get_bullet_density()
        self.bullets.is_primary_bullet_page_properties()
        for attr, value in self.bullets.__dict__.items():
            if attr in ("all_bullets"):
                continue
            setattr(self, attr, value)

    def process_content_data(self):
        """
        Process content data to extract various elements like backlinks, tags, and properties.
        """
        # If no content, return
        if not self.content:
            return

        # Mask code blocks to avoid interference with pattern matching
        masked_content, masked_blocks = self.mask_blocks(self.content)
        self.masked_blocks = masked_blocks

        primary_data = {
            Criteria.INLINE_CODE_BLOCKS.value: find_all_lower(CodePatterns().inline_code_block, self.content),
            Criteria.ASSETS.value: find_all_lower(ContentPatterns().asset, self.content),
            Criteria.ANY_LINKS.value: find_all_lower(ContentPatterns().any_link, self.content),
            Criteria.BLOCKQUOTES.value: find_all_lower(ContentPatterns().blockquote, masked_content),
            Criteria.DRAWS.value: find_all_lower(ContentPatterns().draw, masked_content),
            Criteria.FLASHCARDS.value: find_all_lower(ContentPatterns().flashcard, masked_content),
            Criteria.PAGE_REFERENCES.value: find_all_lower(ContentPatterns().page_reference, masked_content),
            Criteria.TAGGED_BACKLINKS.value: find_all_lower(ContentPatterns().tagged_backlink, masked_content),
            Criteria.TAGS.value: find_all_lower(ContentPatterns().tag, masked_content),
            Criteria.DYNAMIC_VARIABLES.value: find_all_lower(ContentPatterns().dynamic_variable, masked_content),
        }

        # Process aliases and property:values
        property_value_all = ContentPatterns().property_value.findall(self.content)
        properties_values = dict(property_value_all)
        if aliases := properties_values.get("alias"):
            aliases = process_aliases(aliases)

        # Process properties
        page_properties = []
        if self.bullets.has_page_properties:
            page_properties = find_all_lower(ContentPatterns().property, self.primary_bullet)
            self.content = "\n".join(self.content_bullets)
        block_properties = find_all_lower(ContentPatterns().property, self.content)
        page_props = split_builtin_user_properties(page_properties)
        block_props = split_builtin_user_properties(block_properties)

        # Process code blocks
        code_blocks_family = self.find_and_process_pattern(CodePatterns())
        primary_data.update(code_blocks_family)

        # Process double parentheses
        double_paren_family = self.find_and_process_pattern(DoubleParenthesesPatterns())
        primary_data.update(double_paren_family)

        # Process external links
        external_links_family = self.find_and_process_pattern(ExternalLinksPatterns())
        primary_data.update(external_links_family)

        # Process embedded links
        embedded_links_family = self.find_and_process_pattern(EmbeddedLinksPatterns())
        primary_data.update(embedded_links_family)

        # Process double curly braces
        double_curly_family = self.find_and_process_pattern(DoubleCurlyBracketsPatterns())
        primary_data.update(double_curly_family)

        # Process advanced commands
        advanced_commands_family = self.find_and_process_pattern(AdvancedCommandPatterns())
        primary_data.update(advanced_commands_family)

        primary_data.update(
            {
                Criteria.ALIASES.value: aliases,
                Criteria.PROPERTIES_BLOCK_BUILTIN.value: block_props["built_in"],
                Criteria.PROPERTIES_BLOCK_USER.value: block_props["user_props"],
                Criteria.PROPERTIES_PAGE_BUILTIN.value: page_props["built_in"],
                Criteria.PROPERTIES_PAGE_USER.value: page_props["user_props"],
                Criteria.PROPERTIES_VALUES.value: properties_values,
            }
        )

        self.check_has_backlinks(primary_data)

    def check_has_backlinks(self, primary_data: Dict[str, str]):
        """
        Checkd has backlinks in the content.

        Args:
            primary_data (Dict[str, str]): Dictionary containing primary data.
        """
        for key, value in primary_data.items():
            if not value:
                continue

            self.data[key] = value

            if self.has_backlinks:
                continue

            if key in ("page_references", "tags", "tagged_backlinks") or "properties" in key:
                self.has_backlinks = True

    def find_and_process_pattern(self, pattern):
        """
        Find and process a specific pattern in the content.

        Args:
            pattern: The pattern to find and process.
        """
        all_pattern = getattr(pattern, "all", None)
        results = find_all_lower(all_pattern, self.content)
        return pattern.process(results)

    def determine_node_type(self) -> str:
        """Helper function to determine node type based on summary data."""
        return {
            (True, True, True, True): "branch",
            (True, True, False, True): "branch",
            (True, True, True, False): "leaf",
            (True, True, False, False): "leaf",
            (False, True, True, False): "leaf",
            (False, True, False, False): "leaf",
            (True, False, True, True): "root",
            (True, False, False, True): "root",
            (True, False, True, False): "orphan_namespace",
            (False, False, True, False): "orphan_namespace_true",
            (True, False, False, False): "orphan_graph",
            (False, False, False, False): "orphan_true",
        }.get((self.has_content, self.is_backlinked, self.is_backlinked_by_ns_only, self.has_backlinks), "other")

    def mask_blocks(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        Mask code blocks and other patterns in the content.

        Args:
            content (str): The content to mask.

        Returns:
            Tuple[str, Dict[str, str]]: Masked content and a dictionary mapping placeholders to original blocks.
        """
        masked_blocks = {}
        masked_content = content

        for match in CodePatterns().all.finditer(masked_content):
            block_id = f"__CODE_BLOCK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in CodePatterns().inline_code_block.finditer(masked_content):
            block_id = f"__INLINE_CODE_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in AdvancedCommandPatterns().all.finditer(masked_content):
            block_id = f"__ADV_COMMAND_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in DoubleCurlyBracketsPatterns().all.finditer(masked_content):
            block_id = f"__DOUBLE_CURLY_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in EmbeddedLinksPatterns().all.finditer(masked_content):
            block_id = f"__EMB_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in ExternalLinksPatterns().all.finditer(masked_content):
            block_id = f"__EXT_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in DoubleParenthesesPatterns().all.finditer(masked_content):
            block_id = f"__DBLPAREN_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        for match in ContentPatterns().any_link.finditer(masked_content):
            block_id = f"__ANY_LINK_{uuid.uuid4()}__"
            masked_blocks[block_id] = match.group(0)
            masked_content = masked_content.replace(match.group(0), block_id)

        return masked_content, masked_blocks

    def unmask_blocks(self, masked_content: str, masked_blocks: Dict[str, str]) -> str:
        """
        Restore the original content by replacing placeholders with their blocks.

        Args:
            masked_content (str): Content with code block placeholders.
            masked_blocks (Dict[str, str]): Mapping of placeholders to original code blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        content = masked_content
        for placeholder, block in masked_blocks.items():
            content = content.replace(placeholder, block)
        return content

    def check_is_backlinked(self, lookup: Set[str]) -> bool:
        """
        Helper function to check if a file is backlinked.

        Args:
            lookup (Set[str]): Set of backlinks to check against.

        Returns:
            bool: True if the file is backlinked, False otherwise.
        """
        try:
            lookup.remove(self.path.name)
            return True
        except KeyError:
            return False
