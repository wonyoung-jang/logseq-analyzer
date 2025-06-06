"""
LogseqFile class to process Logseq files.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generator

import logseq_analyzer.patterns.adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.patterns.code as CodePatterns
import logseq_analyzer.patterns.content as ContentPatterns
import logseq_analyzer.patterns.double_curly as DoubleCurlyBracketsPatterns
import logseq_analyzer.patterns.double_parentheses as DoubleParenthesesPatterns
import logseq_analyzer.patterns.embedded_links as EmbeddedLinksPatterns
import logseq_analyzer.patterns.external_links as ExternalLinksPatterns

from ..utils.enums import Core, Criteria, Node
from .bullets import LogseqBullets
from .info import LogseqFileInfo
from .stats import LogseqPath


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
        replace_content = content.replace
        blocks = self.blocks
        for placeholder, block in blocks.items():
            content = replace_content(placeholder, block)
        self.content = content


@dataclass
class NodeType:
    """Class to hold node type data."""

    has_backlinks: bool = field(default=False, init=False)
    backlinked: bool = field(default=False, init=False)
    backlinked_ns_only: bool = field(default=False, init=False)
    node_type: str = field(default=Node.OTHER, init=False)

    def check_backlinked(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked and update the node state."""
        if not self.backlinked:
            self.backlinked = NodeType._check_for_backlinks(name, lookup)

    def check_backlinked_ns_only(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked only in its namespace and update the node state."""
        if not self.backlinked_ns_only and NodeType._check_for_backlinks(name, lookup):
            self.backlinked_ns_only = True
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
                n = Node.BRANCH
            case (True, True, True, False):
                n = Node.BRANCH
            case (True, True, False, True):
                n = Node.BRANCH
            case (True, True, False, False):
                n = Node.ROOT
            case (True, False, True, True):
                n = Node.LEAF
            case (True, False, True, False):
                n = Node.LEAF
            case (True, False, False, True):
                n = Node.ORPHAN_NAMESPACE
            case (True, False, False, False):
                n = Node.ORPHAN_GRAPH
            case (False, False, True, True):
                n = Node.LEAF
            case (False, False, True, False):
                n = Node.LEAF
            case (False, False, False, True):
                n = Node.ORPHAN_NAMESPACE_TRUE
            case (False, False, False, False):
                n = Node.ORPHAN_TRUE
        self.node_type = n


class LogseqFile:
    """A class to represent a Logseq file."""

    __slots__ = (
        "path",
        "data",
        "bullets",
        "masked",
        "node",
        "info",
        "is_hls",
    )

    _BACKLINK_CRITERIA: frozenset[str] = frozenset(
        {
            Criteria.PROP_VALUES,
            Criteria.PROP_BLOCK_BUILTIN,
            Criteria.PROP_BLOCK_USER,
            Criteria.PROP_PAGE_BUILTIN,
            Criteria.PROP_PAGE_USER,
            Criteria.CON_PAGE_REF,
            Criteria.CON_TAGGED_BACKLINK,
            Criteria.CON_TAG,
        }
    )

    _PRIMARY_DATA_MAP: dict[str, Any] = {
        Criteria.CON_BLOCKQUOTES: ContentPatterns.BLOCKQUOTE,
        Criteria.CON_DRAW: ContentPatterns.DRAW,
        Criteria.CON_FLASHCARD: ContentPatterns.FLASHCARD,
        Criteria.CON_PAGE_REF: ContentPatterns.PAGE_REFERENCE,
        Criteria.CON_TAGGED_BACKLINK: ContentPatterns.TAGGED_BACKLINK,
        Criteria.CON_TAG: ContentPatterns.TAG,
        Criteria.CON_DYNAMIC_VAR: ContentPatterns.DYNAMIC_VARIABLE,
    }

    _PATTERN_MASKING = (
        (CodePatterns.ALL.sub, f"__{Criteria.COD_INLINE}_"),
        (CodePatterns.INLINE_CODE_BLOCK.sub, f"__{Criteria.COD_INLINE}_"),
        (AdvancedCommandPatterns.ALL.sub, f"__{Criteria.ADV_CMD}_"),
        (DoubleCurlyBracketsPatterns.ALL.sub, f"__{Criteria.DBC_ALL}_"),
        (EmbeddedLinksPatterns.ALL.sub, f"__{Criteria.EMB_LINK_OTHER}_"),
        (ExternalLinksPatterns.ALL.sub, f"__{Criteria.EXT_LINK_OTHER}_"),
        (DoubleParenthesesPatterns.ALL.sub, f"__{Criteria.DBP_ALL_REFS}_"),
        (ContentPatterns.ANY_LINK.sub, f"__{Criteria.CON_ANY_LINKS}_"),
    )

    def __init__(self, path: Path) -> None:
        """Initialize the LogseqFile object."""
        self.path: LogseqPath = LogseqPath(path)
        self.node: NodeType = NodeType()
        self.bullets: LogseqBullets = None
        self.masked: MaskedBlocks = MaskedBlocks()
        self.data: dict[str, Any] = {}
        self.info: LogseqFileInfo = None
        self.is_hls: bool = False

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}({self.path.name})"

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}: {self.path.name}"

    def __hash__(self) -> int:
        return hash(self.path.file.parts)

    def __eq__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.file.parts == other.path.file.parts
        return NotImplemented

    def __lt__(self, other) -> bool:
        if isinstance(other, LogseqFile):
            return self.path.name < other.path.name
        if isinstance(other, str):
            return self.path.name < other
        return NotImplemented

    def process(self) -> None:
        """Process the Logseq file to extract metadata and content."""
        self.init_file_data()
        self.process_content_data()

    def init_file_data(self, hls_prefix: str = Core.HLS_PREFIX) -> None:
        """Extract metadata from a file."""
        self.path.process()
        self.bullets = LogseqBullets(self.path.read_text())
        self.bullets.process()
        self.info = LogseqFileInfo(
            timestamp=self.path.get_timestamp_info(),
            size=self.path.get_size_info(),
            namespace=self.path.get_namespace_info(),
            bullet=self.bullets.get_bullet_info(),
        )
        self.is_hls = self.path.name.startswith(hls_prefix)

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        if not self.info.size.has_content:
            return
        self.mask_blocks()
        self.extract_data()
        self.check_has_backlinks()

    def extract_data_pairs(self) -> Generator[tuple[str, Any]]:
        """
        Extract data pairs from the Logseq file.
        """
        yield from self.extract_primary_data()
        yield from self.bullets.extract_primary_raw_data()
        yield from self.bullets.extract_aliases_and_propvalues()
        yield from self.bullets.extract_properties()
        yield from self.bullets.extract_patterns()

    def extract_data(self) -> None:
        """
        Extract data from the Logseq file.
        """
        self.data.update(dict(self.extract_data_pairs()))

    def mask_blocks(self) -> str:
        """
        Mask code blocks and other patterns in the content.
        """
        content = self.bullets.content
        blocks = self.masked.blocks
        pattern_masking = LogseqFile._PATTERN_MASKING
        _uuid4 = uuid.uuid4

        for sub_regex, prefix in pattern_masking:

            def _repl(match, prefix=prefix) -> str:
                placeholder = f"{prefix}{_uuid4()}__"
                blocks[placeholder] = match.group(0)
                return placeholder

            content = sub_regex(_repl, content)

        self.masked.content = content

    def extract_primary_data(self) -> Generator[tuple[str, Any]]:
        """Extract primary data from the content."""
        _content = self.masked.content
        _primary_data_map = LogseqFile._PRIMARY_DATA_MAP.items()
        for key, value in _primary_data_map:
            if value.search(_content):
                yield key, value.findall(_content)

    def check_has_backlinks(self) -> None:
        """Check has backlinks in the content."""
        self.node.has_backlinks = not LogseqFile._BACKLINK_CRITERIA.isdisjoint(self.data.keys())
