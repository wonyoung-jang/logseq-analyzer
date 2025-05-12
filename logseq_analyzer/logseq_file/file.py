"""
LogseqFile class to process Logseq files.
"""

import uuid
from pathlib import Path

from ..config.builtin_properties import split_builtin_user_properties
from ..utils.enums import Criteria
from ..utils.helpers import find_all_lower, process_aliases
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

    def __init__(self, file_path: Path):
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.file_path: Path = file_path
        self.path: LogseqFilename = LogseqFilename(file_path)
        self.stat: LogseqFilestats = LogseqFilestats(file_path)
        self.bullets: LogseqBullets = LogseqBullets(file_path)
        self.content: str = ""
        self.data: dict = {}
        self.primary_bullet: str = ""
        self.content_bullets: list = []
        self.has_content: bool = False
        self.has_backlinks: bool = False
        self.is_backlinked: bool = False
        self.is_backlinked_by_ns_only: bool = False
        self.node_type: str = "other"
        self.file_type: str = "other"

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
        self.path.file_type = self.path.determine_file_type()
        self.path.name = self.path.process_logseq_filename()
        self.path.is_namespace = self.path.check_is_namespace()
        self.path.is_hls = self.path.check_is_hls()
        self.path.logseq_url = self.path.convert_uri_to_logseq_url()
        self.path.get_namespace_name_data()
        for attr, value in self.path.__dict__.items():
            setattr(self, attr, value)

        for attr, value in self.stat.__dict__.items():
            setattr(self, attr, value)

        self.bullets.content = self.bullets.get_content()
        self.bullets.char_count = self.bullets.get_char_count()
        self.bullets.all_bullets = self.bullets.get_bullet_content()
        self.bullets.primary_bullet = self.bullets.get_primary_bullet()
        self.bullets.bullet_density = self.bullets.get_bullet_density()
        self.bullets.has_page_properties = self.bullets.is_primary_bullet_page_properties()
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
        # Process aliases and properties
        page_properties = []
        if self.bullets.has_page_properties:
            page_properties = find_all_lower(ContentPatterns().property, self.primary_bullet)
            self.content = "\n".join(self.content_bullets)
        block_properties = find_all_lower(ContentPatterns().property, self.content)
        page_props = split_builtin_user_properties(page_properties)
        block_props = split_builtin_user_properties(block_properties)
        aliases_and_properties = {
            Criteria.ALIASES.value: aliases,
            Criteria.PROPERTIES_BLOCK_BUILTIN.value: block_props.get("built_ins", []),
            Criteria.PROPERTIES_BLOCK_USER.value: block_props.get("user_props", []),
            Criteria.PROPERTIES_PAGE_BUILTIN.value: page_props.get("built_ins", []),
            Criteria.PROPERTIES_PAGE_USER.value: page_props.get("user_props", []),
            Criteria.PROPERTIES_VALUES.value: properties_values,
        }
        primary_data.update(aliases_and_properties)
        # Process specific families of patterns
        code_blocks_family = self.find_and_process_pattern(CodePatterns())
        double_paren_family = self.find_and_process_pattern(DoubleParenthesesPatterns())
        external_links_family = self.find_and_process_pattern(ExternalLinksPatterns())
        embedded_links_family = self.find_and_process_pattern(EmbeddedLinksPatterns())
        double_curly_family = self.find_and_process_pattern(DoubleCurlyBracketsPatterns())
        advanced_commands_family = self.find_and_process_pattern(AdvancedCommandPatterns())
        capture_families = [
            code_blocks_family,
            double_paren_family,
            external_links_family,
            embedded_links_family,
            double_curly_family,
            advanced_commands_family,
        ]
        for family in capture_families:
            primary_data.update(family)
        self.check_has_backlinks(primary_data)

    def check_has_backlinks(self, primary_data: dict[str, str]):
        """
        Check has backlinks in the content.

        Args:
            primary_data (dict[str, str]): Dictionary containing primary data.
        """
        for key, value in primary_data.items():
            if value:
                self.data[key] = value
            if not self.has_backlinks and (
                key in ("page_references", "tags", "tagged_backlinks") or "properties" in key
            ):
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
            (True, False, False, True): "root",
            (True, False, True, False): "orphan_namespace",
            (False, False, True, False): "orphan_namespace_true",
            (True, False, False, False): "orphan_graph",
            (False, False, False, False): "orphan_true",
        }.get((self.has_content, self.is_backlinked, self.is_backlinked_by_ns_only, self.has_backlinks), "other")

    def mask_blocks(self, content: str) -> tuple[str, dict[str, str]]:
        """
        Mask code blocks and other patterns in the content.

        Args:
            content (str): The content to mask.

        Returns:
            tuple[str, dict[str, str]]: Masked content and a dictionary mapping placeholders to original blocks.
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
