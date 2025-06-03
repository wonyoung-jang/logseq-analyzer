"""
LogseqFile class to process Logseq files.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import logseq_analyzer.patterns.adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.patterns.code as CodePatterns
import logseq_analyzer.patterns.content as ContentPatterns
import logseq_analyzer.patterns.double_curly as DoubleCurlyBracketsPatterns
import logseq_analyzer.patterns.double_parentheses as DoubleParenthesesPatterns
import logseq_analyzer.patterns.embedded_links as EmbeddedLinksPatterns
import logseq_analyzer.patterns.external_links as ExternalLinksPatterns

from ..utils.enums import Core, Criteria, NodeTypes
from .bullets import LogseqBullets
from .stats import LogseqPath

if TYPE_CHECKING:
    from .stats import NamespaceInfo


@dataclass
class MaskedBlocks:
    """Class to hold masked blocks data."""

    content: str = ""
    blocks: dict[str, str] = field(default_factory=dict)

    def unmask_blocks(self):
        """
        Restore the original content by replacing placeholders with their blocks.
        """
        content = self.content
        blocks = self.blocks
        for placeholder, block in blocks.items():
            content = content.replace(placeholder, block)
        self.content = content


@dataclass
class NodeType:
    """Class to hold node type data."""

    has_backlinks: bool = False
    backlinked: bool = False
    backlinked_ns_only: bool = False
    node_type: str = NodeTypes.OTHER.value

    def check_backlinked(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked and update the node state."""
        self.backlinked = NodeType._check_for_backlinks(name, lookup)

    def check_backlinked_ns_only(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked only in its namespace and update the node state."""
        self.backlinked_ns_only = NodeType._check_for_backlinks(name, lookup)
        if self.backlinked_ns_only:
            self.backlinked = False

    @staticmethod
    def _check_for_backlinks(name: str, lookup: set[str]) -> bool:
        """Helper function to check if a file is backlinked."""
        try:
            lookup.remove(name)
            return True
        except KeyError:
            return False

    def determine_node_type(self, has_content: bool) -> None:
        """Helper function to determine node type based on summary data."""
        has_backlinks = self.has_backlinks
        backlinked = self.backlinked
        backlinked_ns_only = self.backlinked_ns_only
        match (has_content, has_backlinks, backlinked, backlinked_ns_only):
            case (True, True, True, True):
                n = NodeTypes.BRANCH.value
            case (True, True, True, False):
                n = NodeTypes.BRANCH.value
            case (True, True, False, True):
                n = NodeTypes.BRANCH.value
            case (True, True, False, False):
                n = NodeTypes.ROOT.value
            case (True, False, True, True):
                n = NodeTypes.LEAF.value
            case (True, False, True, False):
                n = NodeTypes.LEAF.value
            case (True, False, False, True):
                n = NodeTypes.ORPHAN_NAMESPACE.value
            case (True, False, False, False):
                n = NodeTypes.ORPHAN_GRAPH.value
            case (False, False, True, True):
                n = NodeTypes.LEAF.value
            case (False, False, True, False):
                n = NodeTypes.LEAF.value
            case (False, False, False, True):
                n = NodeTypes.ORPHAN_NAMESPACE_TRUE.value
            case (False, False, False, False):
                n = NodeTypes.ORPHAN_TRUE.value
        self.node_type = n

    def update_asset_backlink(self, asset_mentions: set[str], names: tuple[str, ...]) -> None:
        """
        Update asset backlink status based on mentions and parent.

        Args:
            asset_mentions (set[str]): Set of asset mentions.
            names (tuple[str, ...]): Names of the files.
        """
        for mention in asset_mentions:
            for n in names:
                if n in mention:
                    self.backlinked = True
                    return


class LogseqFile:
    """A class to represent a Logseq file."""

    __slots__ = (
        "_is_namespace",
        "path",
        "data",
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
        self.path: LogseqPath = LogseqPath(path)
        self.node: NodeType = NodeType()
        self.bullets: LogseqBullets = None
        self.masked: MaskedBlocks = MaskedBlocks()
        self.data: dict[str, Any] = {}

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.name})"

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.name}"

    def __hash__(self) -> int:
        return hash(self.path.parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.parts == other.path.parts
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.name < other.name
        if isinstance(other, str):
            return self.name < other
        return NotImplemented

    @property
    def name(self) -> str:
        """Return the name of the Logseq file."""
        return self.path.name

    @property
    def file_type(self) -> str:
        """Return the type of the Logseq file."""
        return self.path.file_type

    @property
    def is_hls(self) -> bool:
        """Check if the Logseq file is a HLS (Hierarchical Link Structure)."""
        return self.name.startswith(Core.HLS_PREFIX.value)

    @property
    def has_content(self) -> bool:
        """Check if the Logseq file has content."""
        return self.path.size_info.has_content

    @property
    def node_type(self) -> str:
        """Return the type of the Logseq file node."""
        return self.node.node_type

    @property
    def has_page_properties(self) -> bool:
        """Check if the Logseq file has page properties."""
        return self.bullets.has_page_properties

    @property
    def uri(self) -> str:
        """Return the URI of the Logseq file."""
        return self.path.uri

    @property
    def logseq_url(self) -> str:
        """Return the Logseq URL of the file."""
        return self.path.logseq_url

    @property
    def suffix(self) -> str:
        """Return the file extension."""
        return self.path.suffix

    @property
    def ns_info(self) -> "NamespaceInfo":
        """Return the namespace information of the Logseq file."""
        return self.path.ns_info

    @property
    def is_namespace(self) -> bool:
        """Check if the filename is a namespace."""
        self._is_namespace = Core.NS_SEP.value in self.name
        return self._is_namespace

    @is_namespace.setter
    def is_namespace(self, value: Any) -> None:
        """Set the is_namespace property."""
        if not isinstance(value, bool):
            raise ValueError("is_namespace must be a boolean value.")
        self._is_namespace = value

    def process(self) -> None:
        """Process the Logseq file to extract metadata and content."""
        self.init_file_data()
        self.process_content_data()

    def init_file_data(self) -> None:
        """Extract metadata from a file."""
        self.path.process()
        self.bullets = LogseqBullets(self.path.read_text())
        self.bullets.process()

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        if not self.has_content:
            return
        self.mask_blocks()
        self.extract_data()
        self.check_has_backlinks()

    def extract_data(self) -> None:
        """
        Extract data from the Logseq file.
        """
        bullets = self.bullets
        self.data.update(
            **dict(self.extract_primary_data()),
            **dict(bullets.extract_primary_raw_data()),
            **dict(bullets.extract_aliases_and_propvalues()),
            **dict(bullets.extract_properties()),
            **dict(bullets.extract_patterns()),
        )

    def mask_blocks(self) -> str:
        """
        Mask code blocks and other patterns in the content.
        """
        content = self.bullets.content
        blocks = self.masked.blocks
        pattern_masking = LogseqFile._PATTERN_MASKING

        for regex, prefix in pattern_masking:

            def _repl(match, prefix=prefix) -> str:
                placeholder = f"{prefix}{uuid.uuid4()}__"
                blocks[placeholder] = match.group(0)
                return placeholder

            content = regex.sub(_repl, content)

        self.masked.content = content

    def extract_primary_data(self) -> Generator[tuple[str, Any]]:
        """Extract primary data from the content."""
        masked_content = self.masked.content
        result = {
            Criteria.CON_BLOCKQUOTES.value: ContentPatterns.BLOCKQUOTE.findall(masked_content),
            Criteria.CON_DRAW.value: ContentPatterns.DRAW.findall(masked_content),
            Criteria.CON_FLASHCARD.value: ContentPatterns.FLASHCARD.findall(masked_content),
            Criteria.CON_PAGE_REF.value: ContentPatterns.PAGE_REFERENCE.findall(masked_content),
            Criteria.CON_TAGGED_BACKLINK.value: ContentPatterns.TAGGED_BACKLINK.findall(masked_content),
            Criteria.CON_TAG.value: ContentPatterns.TAG.findall(masked_content),
            Criteria.CON_DYNAMIC_VAR.value: ContentPatterns.DYNAMIC_VARIABLE.findall(masked_content),
            Criteria.CON_BOLD.value: ContentPatterns.BOLD.findall(masked_content),
        }
        for key, value in {k: v for k, v in result.items() if v}.items():
            yield (key, value)

    def check_has_backlinks(self) -> None:
        """
        Check has backlinks in the content.
        """
        if not LogseqFile._BACKLINK_CRITERIA.isdisjoint(self.data.keys()):
            self.node.has_backlinks = True
