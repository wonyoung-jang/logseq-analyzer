"""
LogseqFile class to process Logseq files.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import logseq_analyzer.utils.patterns_adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.utils.patterns_code as CodePatterns
import logseq_analyzer.utils.patterns_double_curly as DoubleCurlyBracketsPatterns
import logseq_analyzer.utils.patterns_double_parentheses as DoubleParenthesesPatterns
import logseq_analyzer.utils.patterns_embedded_links as EmbeddedLinksPatterns
import logseq_analyzer.utils.patterns_external_links as ExternalLinksPatterns
import logseq_analyzer.utils.patterns_content as ContentPatterns
from ..config.builtin_properties import get_builtin_properties, get_user_properties
from ..utils.enums import Criteria, Nodes
from ..utils.helpers import process_aliases, yield_attrs, process_pattern_hierarchy
from .bullets import LogseqBullets
from .name import LogseqFilename
from .stats import LogseqFilestats


@dataclass
class MaskedBlocks:
    """Class to hold masked blocks data."""

    content: str = ""
    blocks: dict[str, str] = field(default_factory=dict)


@dataclass
class NodeType:
    """Class to hold node type data."""

    has_backlinks: bool = False
    is_backlinked: bool = False
    is_backlinked_by_ns_only: bool = False
    type: str = Nodes.OTHER.value


class LogseqFile:
    """A class to represent a Logseq file."""

    __slots__ = (
        "file_path",
        "data",
        "path",
        "stat",
        "bullets",
        "masked",
        "node",
        "__dict__",
    )

    def __init__(self, file_path: Path) -> None:
        """
        Initialize the LogseqFile object.

        Args:
            file_path (Path): The path to the Logseq file.
        """
        self.file_path: Path = file_path
        self.data: dict[str, Any] = {}
        self.path: LogseqFilename = LogseqFilename(file_path)
        self.stat: LogseqFilestats = LogseqFilestats(file_path)
        self.bullets: LogseqBullets = LogseqBullets(file_path)
        self.masked: MaskedBlocks = MaskedBlocks()
        self.node: NodeType = NodeType()

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

    @property
    def has_backlinks(self) -> bool:
        """Return whether the file has backlinks."""
        return self.node.has_backlinks

    @property
    def node_type(self) -> str:
        """Return the node type."""
        return self.node.type

    @property
    def is_backlinked(self) -> bool:
        """Return whether the file is backlinked."""
        return self.node.is_backlinked

    @property
    def is_backlinked_by_ns_only(self) -> bool:
        """Return whether the file is backlinked by namespace only."""
        return self.node.is_backlinked_by_ns_only

    def init_file_data(self) -> None:
        """Extract metadata from a file."""
        self.path.process_filename()
        self.stat.process_stats()
        self.bullets.process_bullets()
        self._set_file_data_attributes()

    def _set_file_data_attributes(self) -> None:
        """Set file data attributes."""
        _large = ("content_bullets", "content")
        for subdata in (self.stat, self.path, self.bullets):
            for attr, value in yield_attrs(subdata):
                if subdata is self.bullets and attr in _large:
                    continue
                setattr(self, attr, value)

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        self.mask_blocks()
        primary_data = self.extract_primary_data()
        primary_data.update(self.extract_aliases_and_propvalues())
        primary_data.update(self.extract_properties())
        primary_data.update(self.extract_patterns())
        self.check_has_backlinks(primary_data)

    def mask_blocks(self) -> None:
        """
        Mask code blocks and other patterns in the content.
        """
        patterns = (
            (CodePatterns.ALL, f"__{Criteria.COD_INLINE.name}_"),
            (CodePatterns.INLINE_CODE_BLOCK, f"__{Criteria.COD_INLINE.name}_"),
            (AdvancedCommandPatterns.ALL, f"__{Criteria.ADV_CMD.name}_"),
            (DoubleCurlyBracketsPatterns.ALL, f"__{Criteria.DBC_ALL.name}_"),
            (EmbeddedLinksPatterns.ALL, f"__{Criteria.EMB_LINK_OTHER.name}_"),
            (ExternalLinksPatterns.ALL, f"__{Criteria.EXT_LINK_OTHER.name}_"),
            (DoubleParenthesesPatterns.ALL, f"__{Criteria.DBP_ALL_REFS.name}_"),
            (ContentPatterns.ANY_LINK, f"__{Criteria.ANY_LINKS.name}_"),
        )

        masked_blocks: dict[str, str] = self.masked.blocks
        masked_content = self.bullets.content

        for regex, prefix in patterns:

            def _repl(match, prefix=prefix) -> str:
                placeholder = f"{prefix}{uuid.uuid4()}__"
                masked_blocks[placeholder] = match.group(0)
                return placeholder

            masked_content = regex.sub(_repl, masked_content)

        self.masked.content = masked_content

    def extract_primary_data(self) -> dict[str, str]:
        """
        Extract primary data from the content.

        Returns:
            dict: A dictionary containing the extracted data.
        """
        content = self.bullets.content
        masked_content = self.masked.content
        return {
            Criteria.COD_INLINE.value: CodePatterns.INLINE_CODE_BLOCK.findall(content),
            Criteria.ANY_LINKS.value: ContentPatterns.ANY_LINK.findall(content),
            Criteria.ASSETS.value: ContentPatterns.ASSET.findall(masked_content),
            Criteria.BLOCKQUOTES.value: ContentPatterns.BLOCKQUOTE.findall(masked_content),
            Criteria.DRAWS.value: ContentPatterns.DRAW.findall(masked_content),
            Criteria.FLASHCARDS.value: ContentPatterns.FLASHCARD.findall(masked_content),
            Criteria.PAGE_REFERENCES.value: ContentPatterns.PAGE_REFERENCE.findall(masked_content),
            Criteria.TAGGED_BACKLINKS.value: ContentPatterns.TAGGED_BACKLINK.findall(masked_content),
            Criteria.TAGS.value: ContentPatterns.TAG.findall(masked_content),
            Criteria.DYNAMIC_VARIABLES.value: ContentPatterns.DYNAMIC_VARIABLE.findall(masked_content),
            Criteria.BOLD.value: ContentPatterns.BOLD.findall(masked_content),
        }

    def extract_aliases_and_propvalues(self) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        content = self.bullets.content
        properties_values = dict(ContentPatterns.PROPERTY_VALUE.findall(content))
        if aliases := properties_values.get("alias"):
            aliases = sorted(process_aliases(aliases))
        return {
            Criteria.ALIASES.value: aliases,
            Criteria.PROP_VALUES.value: properties_values,
        }

    def extract_properties(self) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        content = self.bullets.content
        page_properties = set()
        block_properties = set()
        if self.bullets.stats.has_page_properties:
            page_properties.update(ContentPatterns.PROPERTY.findall(self.bullets.primary_bullet))
            content = "\n".join(self.bullets.content_bullets)
        block_properties.update(ContentPatterns.PROPERTY.findall(content))
        self.bullets.content = content
        page_props_builtins = sorted(get_builtin_properties(page_properties))
        page_props_user = sorted(get_user_properties(page_properties))
        block_props_builtins = sorted(get_builtin_properties(block_properties))
        block_props_user = sorted(get_user_properties(block_properties))
        return {
            Criteria.PROP_BLOCK_BUILTIN.value: block_props_builtins,
            Criteria.PROP_BLOCK_USER.value: block_props_user,
            Criteria.PROP_PAGE_BUILTIN.value: page_props_builtins,
            Criteria.PROP_PAGE_USER.value: page_props_user,
        }

    def extract_patterns(self) -> dict[str, Any]:
        """
        Process patterns in the content.

        Returns:
            dict: A dictionary containing the processed patterns.
        """
        patterns = (
            AdvancedCommandPatterns,
            CodePatterns,
            DoubleCurlyBracketsPatterns,
            DoubleParenthesesPatterns,
            EmbeddedLinksPatterns,
            ExternalLinksPatterns,
        )
        result = {}
        content = self.bullets.content
        for pattern in patterns:
            processed_patterns = process_pattern_hierarchy(content, pattern)
            result.update(processed_patterns)

        return result

    def check_has_backlinks(self, primary_data: dict[str, str]) -> None:
        """
        Check has backlinks in the content.

        Args:
            primary_data (dict[str, str]): Dictionary containing primary data.
        """
        data = self.data
        has_backlinks = self.node.has_backlinks
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
        self.node.has_backlinks = has_backlinks

    def determine_node_type(self) -> None:
        """Helper function to determine node type based on summary data."""
        if self.stat.has_content:
            self.node.type = self.check_node_type_has_content()
        else:
            self.node.type = self.check_node_type_has_no_content()

    def check_node_type_has_content(self) -> str:
        """
        Helper function to check node type based on content.
        """
        if self.node.has_backlinks:
            if self.node.is_backlinked or self.node.is_backlinked_by_ns_only:
                node_type = Nodes.BRANCH.value
            else:
                node_type = Nodes.ROOT.value
        elif self.node.is_backlinked:
            node_type = Nodes.LEAF.value
        elif self.node.is_backlinked_by_ns_only and not self.node.is_backlinked:
            node_type = Nodes.ORPHAN_NAMESPACE.value
        else:
            node_type = Nodes.ORPHAN_GRAPH.value
        return node_type

    def check_node_type_has_no_content(self) -> str:
        """
        Helper function to check node type based on no content.
        """
        if self.node.is_backlinked:
            node_type = Nodes.LEAF.value
        elif self.node.is_backlinked_by_ns_only and not self.node.is_backlinked:
            node_type = Nodes.ORPHAN_NAMESPACE_TRUE.value
        else:
            node_type = Nodes.ORPHAN_TRUE.value
        return node_type

    def unmask_blocks(self) -> str:
        """
        Restore the original content by replacing placeholders with their blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        content = self.masked.content
        masked_blocks = self.masked.blocks
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

    def set_ns_data(self) -> None:
        """Set namespace data for a file."""
        for attr, value in yield_attrs(self.path):
            if attr.startswith("ns_") or attr == "is_namespace":
                setattr(self, attr, value)

    def update_asset_backlink(self, asset_mentions: list[str], parent: str) -> None:
        """
        Update asset backlink status based on mentions and parent.

        Args:
            asset_mentions (list[str]): List of asset mentions.
            parent (str): Parent file name.
        """
        nameset = (self.path.name, parent)
        for asset_mention in asset_mentions:
            if any(name in asset_mention for name in nameset):
                self.node.is_backlinked = True
                return
