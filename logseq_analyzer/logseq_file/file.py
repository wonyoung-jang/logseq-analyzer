"""LogseqFile class to process Logseq files."""

import uuid
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any

import logseq_analyzer.patterns.content as content_patterns
from logseq_analyzer.patterns import adv_cmd, code

from ..utils.enums import Core, CritAdvCmd, CritCode, CritContent, CritProp
from .bullets import LogseqBullets
from .info import LogseqFileInfo, NodeType
from .stats import LogseqPath

if TYPE_CHECKING:
    import re
    from collections.abc import Generator
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
    CritContent.BLOCKQUOTES: content_patterns.BLOCKQUOTE,
    CritContent.DRAW: content_patterns.DRAW,
    CritContent.FLASHCARD: content_patterns.FLASHCARD,
    CritContent.PAGE_REF: content_patterns.PAGE_REFERENCE,
    CritContent.TAGGED_BACKLINK: content_patterns.TAGGED_BACKLINK,
    CritContent.TAG: content_patterns.TAG,
    CritContent.DYNAMIC_VAR: content_patterns.DYNAMIC_VARIABLE,
}

PATTERN_MASKING = (
    (code.ALL.sub, f"__{CritCode.ML_ALL}_"),
    (code.INLINE_CODE_BLOCK.sub, f"__{CritCode.INLINE}_"),
    (adv_cmd.ALL.sub, f"__{CritAdvCmd.ALL}_"),
    (content_patterns.ANY_LINK.sub, f"__{CritContent.ANY_LINKS}_"),
)


@dataclass(slots=True)
class MaskedBlocks:
    """Class to hold masked blocks data."""

    content: str = ""
    blocks: dict[str, str] = field(default_factory=dict)

    def unmask_blocks(self) -> None:
        """Restore the original content by replacing placeholders with their blocks."""
        content = self.content
        replace_content = content.replace
        for placeholder, block in self.blocks.items():
            content = replace_content(placeholder, block)
        self.content = content


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
        self.path: LogseqPath = LogseqPath(path_input)

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
        self.init_file_data()
        self.process_content_data()

    def init_file_data(self) -> None:
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
        self.is_hls = self.path.name.startswith(Core.HLS_PREFIX)

    def process_content_data(self) -> None:
        """Process content data to extract various elements like backlinks, tags, and properties."""
        if not self.info.size.has_content:
            return
        self.mask_blocks()
        self.extract_data()
        self.check_has_backlinks()

    def extract_data_pairs(self) -> Generator[tuple[str, Any]]:
        """Extract data pairs from the Logseq file."""
        yield from self.extract_primary_data()
        yield from self.bullets.extract_primary_raw_data()
        yield from self.bullets.extract_aliases_and_propvalues()
        yield from self.bullets.extract_properties()
        yield from self.bullets.extract_patterns()

    def extract_data(self) -> None:
        """Extract data from the Logseq file."""
        self.data.update(dict(self.extract_data_pairs()))

    def mask_blocks(self) -> None:
        """Mask code blocks and other patterns in the content."""
        content = self.bullets.content
        blocks = {}
        pattern_masking = PATTERN_MASKING
        _uuid4 = uuid.uuid4

        for sub_regex, prefix in pattern_masking:

            def _repl(match: re.Match, prefix: str = prefix) -> str:
                placeholder = f"{prefix}{_uuid4()}__"
                blocks[placeholder] = match.group(0)
                return placeholder

            content = sub_regex(_repl, content)

        self.masked: MaskedBlocks = MaskedBlocks(
            content=content,
            blocks=blocks,
        )

    def extract_primary_data(self) -> Generator[tuple[str, Any]]:
        """Extract primary data from the content."""
        _content = self.masked.content
        _primary_data_map = PRIMARY_DATA_MAP.items()
        for key, value in _primary_data_map:
            if value.search(_content):
                yield key, value.findall(_content)

    def check_has_backlinks(self) -> None:
        """Check has backlinks in the content."""
        self.node.has_backlinks = not BACKLINK_CRITERIA.isdisjoint(self.data.keys())
