"""LogseqFile class to process Logseq files."""

import uuid
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.logseq_file.bullets import LogseqBullets
from logseq_analyzer.logseq_file.info import LogseqFileInfo, NodeType
from logseq_analyzer.logseq_file.stats import LogseqPath
from logseq_analyzer.patterns.content import ContentPatterns
from logseq_analyzer.patterns.patterns import AdvCmdPatterns, CodePatterns
from logseq_analyzer.utils.enums import Core, CritAdvCmd, CritCode, CritContent, CritProp

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator
    from pathlib import Path

BACKLINK_CRITERIA: frozenset[str] = frozenset(
    {
        CritProp.VALUES,
        CritProp.BLOCK_BUILTIN,
        CritProp.BLOCK_USER,
        CritProp.PAGE_BUILTIN,
        CritProp.PAGE_USER,
        CritContent.PAGE_REF,
        CritContent.TAGGED_BACKLINK,
        CritContent.TAG,
    }
)
PRIMARY_DATA_MAP: dict[str, re.Pattern] = {
    CritContent.BLOCKQUOTES: ContentPatterns.BLOCKQUOTE,
    CritContent.DRAW: ContentPatterns.DRAW,
    CritContent.FLASHCARD: ContentPatterns.FLASHCARD,
    CritContent.PAGE_REF: ContentPatterns.PAGE_REFERENCE,
    CritContent.TAGGED_BACKLINK: ContentPatterns.TAGGED_BACKLINK,
    CritContent.TAG: ContentPatterns.TAG,
    CritContent.DYNAMIC_VAR: ContentPatterns.DYNAMIC_VARIABLE,
}
PATTERN_MASKING = (
    (CodePatterns.ALL.sub, f"__{CritCode.ML_ALL}_"),
    (ContentPatterns.INLINE_CODE_BLOCK.sub, f"__{CritCode.INLINE}_"),
    (AdvCmdPatterns.ALL.sub, f"__{CritAdvCmd.ALL}_"),
    (ContentPatterns.ANY_LINK.sub, f"__{CritContent.ANY_LINKS}_"),
)


@dataclass(slots=True)
class MaskedBlocks:
    """Class to hold masked blocks data."""

    content: str = ""
    blocks: dict[str, str] = field(default_factory=dict)

    def mask(self, content: str) -> None:
        """Mask code blocks and other patterns in the content."""
        self.content = content
        for sub_regex, prefix in PATTERN_MASKING:

            def _repl(match: re.Match, prefix: str = prefix) -> str:
                placeholder = f"{prefix}{uuid.uuid4()}__"
                self.blocks[placeholder] = match.group(0)
                return placeholder

            self.content = sub_regex(_repl, self.content)

    def extract_primary_data(self) -> Iterator[tuple[str, Any]]:
        """Extract primary data from the content."""
        for key, value in PRIMARY_DATA_MAP.items():
            if value.search(self.content):
                yield key, value.findall(self.content)

    def unmask_blocks(self) -> None:
        """Restore the original content by replacing placeholders with their blocks."""
        for placeholder, block in self.blocks.items():
            self.content = self.content.replace(placeholder, block)


@dataclass(slots=True)
class LogseqFile:
    """A class to represent a Logseq file."""

    path_input: InitVar[Path]
    path: LogseqPath = field(init=False)
    data: dict[str, Any] = field(default_factory=dict)
    bullets: LogseqBullets = field(init=False)
    masked: MaskedBlocks = field(default_factory=MaskedBlocks)
    node: NodeType = field(default_factory=NodeType)
    info: LogseqFileInfo = field(init=False)
    is_hls: bool = False

    def __post_init__(self, path_input: Path) -> None:
        """Initialize the LogseqFile object."""
        self.path = LogseqPath(path_input)

    def __hash__(self) -> int:
        """Return the hash of the LogseqFile based on its path."""
        return hash(self.path.file.parts)

    def __eq__(self, other: object) -> bool:
        """Check equality based on the file path."""
        if isinstance(other, LogseqFile):
            return self.path.file.parts == other.path.file.parts
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        """Compare LogseqFile objects based on their file names."""
        if isinstance(other, LogseqFile):
            return self.path.name < other.path.name
        if isinstance(other, str):
            return self.path.name < other
        return NotImplemented

    def process(self) -> None:
        """Process the Logseq file to extract metadata and content."""
        self.bullets = LogseqBullets(self.path.read_text())
        self.info = LogseqFileInfo(
            timestamp=self.path.get_timestamp_info(),
            size=self.path.get_size_info(),
            namespace=self.path.get_namespace_info(),
            bullet=self.bullets.get_bullet_info(),
        )
        self.is_hls = self.path.name.startswith(Core.HLS_PREFIX)
        if not self.info.size.has_content:
            return
        self.masked.mask(self.bullets.content)
        self.data.update(self.masked.extract_primary_data())
        self.data.update(self.bullets.extract_primary_raw_data())
        self.data.update(self.bullets.extract_aliases_and_propvalues())
        self.data.update(self.bullets.extract_properties())
        self.data.update(self.bullets.extract_patterns())
        self.node.has_backlinks = not BACKLINK_CRITERIA.isdisjoint(self.data.keys())
