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

from ..utils.enums import Core, Criteria, FileType, Node
from .bullets import LogseqBullets
from .stats import LogseqPath, NamespaceInfo, SizeInfo, TimestampInfo


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
    node_type: str = field(default=Node.OTHER.value, init=False)

    def check_backlinked(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked and update the node state."""
        if not self.backlinked:
            self.backlinked = NodeType._check_for_backlinks(name, lookup)

    def check_backlinked_ns_only(self, name: str, lookup: set[str]) -> None:
        """Check if a file is backlinked only in its namespace and update the node state."""
        if not self.backlinked_ns_only:
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
                n = Node.BRANCH.value
            case (True, True, True, False):
                n = Node.BRANCH.value
            case (True, True, False, True):
                n = Node.BRANCH.value
            case (True, True, False, False):
                n = Node.ROOT.value
            case (True, False, True, True):
                n = Node.LEAF.value
            case (True, False, True, False):
                n = Node.LEAF.value
            case (True, False, False, True):
                n = Node.ORPHAN_NAMESPACE.value
            case (True, False, False, False):
                n = Node.ORPHAN_GRAPH.value
            case (False, False, True, True):
                n = Node.LEAF.value
            case (False, False, True, False):
                n = Node.LEAF.value
            case (False, False, False, True):
                n = Node.ORPHAN_NAMESPACE_TRUE.value
            case (False, False, False, False):
                n = Node.ORPHAN_TRUE.value
        self.node_type = n


@dataclass
class LogseqFileInfo:
    """LogseqFileInfo class."""

    timestamp: TimestampInfo
    size: SizeInfo
    namespace: NamespaceInfo


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
        self.set_is_hls()

    def set_is_hls(self, hls_prefix: str = Core.HLS_PREFIX.value) -> None:
        """Check if the file is an HLS file."""
        self.is_hls = self.path.name.startswith(hls_prefix)

    def init_file_data(self) -> None:
        """Extract metadata from a file."""
        self.path.process()
        self.info = LogseqFileInfo(
            timestamp=self.path.get_timestamp_info(),
            size=self.path.get_size_info(),
            namespace=self.path.get_namespace_info(),
        )
        self.bullets = LogseqBullets(self.path.read_text())
        self.bullets.process()

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        if not self.info.size.has_content:
            return
        if self.path.file_type not in (FileType.JOURNAL.value, FileType.PAGE.value):
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
        _uuid4 = uuid.uuid4

        for regex, prefix in pattern_masking:

            def _repl(match, prefix=prefix) -> str:
                placeholder = f"{prefix}{_uuid4()}__"
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
            # Criteria.CON_BOLD.value: ContentPatterns.BOLD.findall(masked_content),
        }

        for key, value in result.items():
            if value:
                yield (key, value)

    def check_has_backlinks(self) -> None:
        """Check has backlinks in the content."""
        if not LogseqFile._BACKLINK_CRITERIA.isdisjoint(self.data.keys()):
            self.node.has_backlinks = True
