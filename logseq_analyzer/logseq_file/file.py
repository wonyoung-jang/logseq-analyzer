"""LogseqFile class to process Logseq files."""

import uuid
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.logseq_file.bullets import LogseqBullets
from logseq_analyzer.logseq_file.info import LogseqFileContext, LogseqFileInfo, NodeType
from logseq_analyzer.logseq_file.stats import LogseqPath
from logseq_analyzer.patterns.content import PRIMARY_DATA_MAP, ContentPatterns
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
MASK_MAP: dict[str, re.Pattern] = {
    CritCode.ML_ALL: CodePatterns.ALL,
    CritCode.INLINE: ContentPatterns.INLINE_CODE_BLOCK,
    CritAdvCmd.ALL: AdvCmdPatterns.ALL,
    CritContent.ANY_LINKS: ContentPatterns.ANY_LINK,
}


@dataclass(slots=True)
class MaskedBlocks:
    """Class to hold masked blocks data."""

    content: str
    blocks: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Mask code blocks and other patterns in the content."""
        for prefix, regex in MASK_MAP.items():

            def _repl(match: re.Match, prefix: str = prefix) -> str:
                placeholder = f"__{prefix}__{uuid.uuid4()}__"
                self.blocks[placeholder] = match.group(0)
                return placeholder

            self.content = regex.sub(_repl, self.content)

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
    context: LogseqFileContext
    data: dict[str, Any] = field(default_factory=dict)
    node: NodeType = field(default_factory=NodeType)
    is_hls: bool = False
    path: LogseqPath = field(init=False)
    bullets: LogseqBullets = field(init=False)
    info: LogseqFileInfo = field(init=False)

    def __post_init__(self, path_input: Path) -> None:
        """Initialize the LogseqFile object."""
        self.path = LogseqPath(path_input, self.context)
        self.bullets = LogseqBullets(self.path.read_text())
        self.info = LogseqFileInfo(
            timestamp=self.path.timestamp_info,
            size=self.path.size_info,
            namespace=self.path.namespace_info,
            bullet=self.bullets.bullet_info,
        )
        self.is_hls = self.path.name.startswith(Core.HLS_PREFIX)
        if not self.info.size.has_content:
            return
        _masked = MaskedBlocks(self.bullets.content)
        self.data.update(_masked.extract_primary_data())
        self.data.update(self.bullets.extract_primary_raw_data())
        self.data.update(self.bullets.extract_aliases_and_propvalues())
        self.data.update(self.bullets.extract_properties())
        self.data.update(self.bullets.extract_patterns())
        self.node.has_backlinks = not BACKLINK_CRITERIA.isdisjoint(self.data.keys())

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

    def yield_attrs(self) -> Iterator[tuple[str, Any]]:
        """Yield the attributes of the LogseqFile."""
        yield "node", self.node
        yield "is_hls", self.is_hls
        yield "path", self.path
        yield "bullets", self.bullets
        yield "info", self.info
