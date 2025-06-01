"""
LogseqFile class to process Logseq files.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import logseq_analyzer.utils.patterns_adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.utils.patterns_code as CodePatterns
import logseq_analyzer.utils.patterns_content as ContentPatterns
import logseq_analyzer.utils.patterns_double_curly as DoubleCurlyBracketsPatterns
import logseq_analyzer.utils.patterns_double_parentheses as DoubleParenthesesPatterns
import logseq_analyzer.utils.patterns_embedded_links as EmbeddedLinksPatterns
import logseq_analyzer.utils.patterns_external_links as ExternalLinksPatterns

from ..utils.enums import Criteria, NodeTypes
from ..utils.helpers import (
    extract_builtin_properties,
    process_aliases,
    process_pattern_hierarchy,
    remove_builtin_properties,
)
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
    backlinked: bool = False
    backlinked_ns_only: bool = False
    type: str = NodeTypes.OTHER.value


class LogseqFile:
    """A class to represent a Logseq file."""

    __slots__ = (
        "path",
        "data",
        "fname",
        "stats",
        "bullets",
        "masked",
        "node",
    )

    _BACKLINK_CRITERIA: frozenset[str] = frozenset(
        {
            Criteria.PROP_VALUES.value,
            Criteria.PROP_BLOCK_BUILTIN.value,
            Criteria.PROP_BLOCK_USER.value,
            Criteria.PROP_PAGE_BUILTIN.value,
            Criteria.PROP_PAGE_USER.value,
            Criteria.CON_PAGE_REF.value,
            Criteria.CON_TAGGED_BACKLINK.value,
            Criteria.CON_TAG.value,
        }
    )

    _PATTERN_MODULES = (
        AdvancedCommandPatterns,
        CodePatterns,
        DoubleCurlyBracketsPatterns,
        DoubleParenthesesPatterns,
        EmbeddedLinksPatterns,
        ExternalLinksPatterns,
    )

    _PATTERN_MASKING = (
        (CodePatterns.ALL, f"__{Criteria.COD_INLINE.name}_"),
        (CodePatterns.INLINE_CODE_BLOCK, f"__{Criteria.COD_INLINE.name}_"),
        (AdvancedCommandPatterns.ALL, f"__{Criteria.ADV_CMD.name}_"),
        (DoubleCurlyBracketsPatterns.ALL, f"__{Criteria.DBC_ALL.name}_"),
        (EmbeddedLinksPatterns.ALL, f"__{Criteria.EMB_LINK_OTHER.name}_"),
        (ExternalLinksPatterns.ALL, f"__{Criteria.EXT_LINK_OTHER.name}_"),
        (DoubleParenthesesPatterns.ALL, f"__{Criteria.DBP_ALL_REFS.name}_"),
        (ContentPatterns.ANY_LINK, f"__{Criteria.CON_ANY_LINKS.name}_"),
    )

    def __init__(self, path: Path) -> None:
        """Initialize the LogseqFile object."""
        self.path: Path = path
        self.stats: LogseqFilestats = LogseqFilestats(path)
        self.node: NodeType = NodeType()
        self.fname: LogseqFilename = LogseqFilename(path)
        self.bullets: LogseqBullets = LogseqBullets(path)
        self.masked: MaskedBlocks = MaskedBlocks()
        self.data: dict[str, Any] = {}

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}(path="{self.path}")'

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.path}"

    def __hash__(self) -> int:
        return hash(self.path.parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.parts == other.path.parts
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.fname.name < other.fname.name
        if isinstance(other, str):
            return self.fname.name < other
        return NotImplemented

    def process(self) -> None:
        """Process the Logseq file to extract metadata and content."""
        self.init_file_data()
        self.process_content_data()

    def init_file_data(self) -> None:
        """Extract metadata from a file."""
        self.fname.process()
        self.stats.process()
        self.bullets.process()

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        if not self.stats.has_content:
            return
        self.mask_blocks()
        data = self.extract_primary_data()
        data.update(self.extract_aliases_and_propvalues())
        data.update(self.extract_properties())
        data.update(self.extract_patterns())
        self.data.update({k: v for k, v in data.items() if v})
        self.check_has_backlinks()

    def mask_blocks(self) -> None:
        """
        Mask code blocks and other patterns in the content.
        """
        self.masked.content = self.bullets.content

        for regex, prefix in self._PATTERN_MASKING:

            def _repl(match, prefix=prefix) -> str:
                placeholder = f"{prefix}{uuid.uuid4()}__"
                self.masked.blocks[placeholder] = match.group(0)
                return placeholder

            self.masked.content = regex.sub(_repl, self.masked.content)

    def extract_primary_data(self) -> dict[str, str]:
        """
        Extract primary data from the content.

        Returns:
            dict: A dictionary containing the extracted data.
        """
        return {
            Criteria.COD_INLINE.value: CodePatterns.INLINE_CODE_BLOCK.findall(self.bullets.content),
            Criteria.CON_ANY_LINKS.value: ContentPatterns.ANY_LINK.findall(self.bullets.content),
            Criteria.CON_ASSETS.value: ContentPatterns.ASSET.findall(self.bullets.content),
            Criteria.CON_BLOCKQUOTES.value: ContentPatterns.BLOCKQUOTE.findall(self.masked.content),
            Criteria.CON_DRAW.value: ContentPatterns.DRAW.findall(self.masked.content),
            Criteria.CON_FLASHCARD.value: ContentPatterns.FLASHCARD.findall(self.masked.content),
            Criteria.CON_PAGE_REF.value: ContentPatterns.PAGE_REFERENCE.findall(self.masked.content),
            Criteria.CON_TAGGED_BACKLINK.value: ContentPatterns.TAGGED_BACKLINK.findall(self.masked.content),
            Criteria.CON_TAG.value: ContentPatterns.TAG.findall(self.masked.content),
            Criteria.CON_DYNAMIC_VAR.value: ContentPatterns.DYNAMIC_VARIABLE.findall(self.masked.content),
            # Criteria.CON_BOLD.value: ContentPatterns.BOLD.findall(self.masked.content),
        }

    def extract_aliases_and_propvalues(self) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        properties_values = dict(ContentPatterns.PROPERTY_VALUE.findall(self.bullets.content))
        if aliases := properties_values.get("alias"):
            aliases = list(process_aliases(aliases))
        return {
            Criteria.CON_ALIASES.value: aliases,
            Criteria.PROP_VALUES.value: properties_values,
        }

    def extract_properties(self) -> dict[str, Any]:
        """
        Extract aliases and properties from the content.

        Returns:
            dict: A dictionary containing the extracted aliases and properties.
        """
        page_props = set()
        if self.bullets.stats.has_page_properties:
            page_props.update(ContentPatterns.PROPERTY.findall(self.bullets.primary_bullet))
            self.bullets.content = "\n".join(self.bullets.content_bullets)
        block_props = set(ContentPatterns.PROPERTY.findall(self.bullets.content))
        return {
            Criteria.PROP_BLOCK_BUILTIN.value: extract_builtin_properties(block_props),
            Criteria.PROP_BLOCK_USER.value: remove_builtin_properties(block_props),
            Criteria.PROP_PAGE_BUILTIN.value: extract_builtin_properties(page_props),
            Criteria.PROP_PAGE_USER.value: remove_builtin_properties(page_props),
        }

    def extract_patterns(self) -> dict[str, Any]:
        """
        Process patterns in the content.

        Returns:
            dict: A dictionary containing the processed patterns.
        """
        result = {}
        for pattern in self._PATTERN_MODULES:
            processed_patterns = process_pattern_hierarchy(self.bullets.content, pattern)
            result.update(processed_patterns)
        return result

    def check_has_backlinks(self) -> None:
        """
        Check has backlinks in the content.
        """
        if self._BACKLINK_CRITERIA.intersection(self.data.keys()):
            self.node.has_backlinks = True

    def determine_node_type(self) -> None:
        """Helper function to determine node type based on summary data."""
        has_content = self.stats.has_content
        has_backlinks = self.node.has_backlinks
        backlinked = self.node.backlinked
        backlinked_ns_only = self.node.backlinked_ns_only
        match (has_content, has_backlinks, backlinked, backlinked_ns_only):
            case (True, True, True, True):
                self.node.type = NodeTypes.BRANCH.value
            case (True, True, True, False):
                self.node.type = NodeTypes.BRANCH.value
            case (True, True, False, True):
                self.node.type = NodeTypes.BRANCH.value
            case (True, True, False, False):
                self.node.type = NodeTypes.ROOT.value
            case (True, False, True, True):
                self.node.type = NodeTypes.LEAF.value
            case (True, False, True, False):
                self.node.type = NodeTypes.LEAF.value
            case (True, False, False, True):
                self.node.type = NodeTypes.ORPHAN_NAMESPACE.value
            case (True, False, False, False):
                self.node.type = NodeTypes.ORPHAN_GRAPH.value
            case (False, False, True, True):
                self.node.type = NodeTypes.LEAF.value
            case (False, False, True, False):
                self.node.type = NodeTypes.LEAF.value
            case (False, False, False, True):
                self.node.type = NodeTypes.ORPHAN_NAMESPACE_TRUE.value
            case (False, False, False, False):
                self.node.type = NodeTypes.ORPHAN_TRUE.value

    def unmask_blocks(self) -> str:
        """
        Restore the original content by replacing placeholders with their blocks.

        Returns:
            str: Original content with code blocks restored.
        """
        for placeholder, block in self.masked.blocks.items():
            self.masked.content = self.masked.content.replace(placeholder, block)
        return self.masked.content

    def check_is_backlinked(self, lookup: set[str]) -> bool:
        """
        Helper function to check if a file is backlinked.

        Args:
            lookup (set[str]): Set of backlinks to check against.

        Returns:
            bool: True if the file is backlinked, False otherwise.
        """
        try:
            lookup.remove(self.fname.name)
            return True
        except KeyError:
            return False

    def update_asset_backlink(self, asset_mentions: list[str], parent: str) -> None:
        """
        Update asset backlink status based on mentions and parent.

        Args:
            asset_mentions (list[str]): List of asset mentions.
            parent (str): Parent file name.
        """
        for asset_mention in asset_mentions:
            for name in (self.fname.name, parent):
                if name in asset_mention:
                    self.node.backlinked = True
                    return
