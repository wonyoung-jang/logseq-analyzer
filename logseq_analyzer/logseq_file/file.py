"""
LogseqFile class to process Logseq files.
"""

import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generator

import logseq_analyzer.patterns.adv_cmd as AdvancedCommandPatterns
import logseq_analyzer.patterns.code as CodePatterns
import logseq_analyzer.patterns.content as ContentPatterns

from ..utils.enums import Core, CritAdvCmd, CritCode, CritContent, CritProp
from .bullets import LogseqBullets
from .info import LogseqFileInfo, NodeType
from .stats import LogseqPath


@dataclass(slots=True)
class MaskedBlocks:
    """Class to hold masked blocks data."""

    content: str
    blocks: dict[str, str]

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

    _PRIMARY_DATA_MAP: dict[str, re.Pattern] = {
        CritContent.BLOCKQUOTES: ContentPatterns.BLOCKQUOTE,
        CritContent.DRAW: ContentPatterns.DRAW,
        CritContent.FLASHCARD: ContentPatterns.FLASHCARD,
        CritContent.PAGE_REF: ContentPatterns.PAGE_REFERENCE,
        CritContent.TAGGED_BACKLINK: ContentPatterns.TAGGED_BACKLINK,
        CritContent.TAG: ContentPatterns.TAG,
        CritContent.DYNAMIC_VAR: ContentPatterns.DYNAMIC_VARIABLE,
    }

    _PATTERN_MASKING = (
        (CodePatterns.ALL.sub, f"__{CritCode.ML_ALL}_"),
        (CodePatterns.INLINE_CODE_BLOCK.sub, f"__{CritCode.INLINE}_"),
        (AdvancedCommandPatterns.ALL.sub, f"__{CritAdvCmd.ALL}_"),
        (ContentPatterns.ANY_LINK.sub, f"__{CritContent.ANY_LINKS}_"),
    )

    def __init__(self, path: Path) -> None:
        """Initialize the LogseqFile object."""
        self.path: LogseqPath = LogseqPath(path)
        self.node: NodeType = NodeType()
        self.bullets: LogseqBullets = None
        self.masked: MaskedBlocks = None
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
        blocks = {}
        pattern_masking = LogseqFile._PATTERN_MASKING
        _uuid4 = uuid.uuid4

        for sub_regex, prefix in pattern_masking:

            def _repl(match, prefix=prefix) -> str:
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
        _primary_data_map = LogseqFile._PRIMARY_DATA_MAP.items()
        for key, value in _primary_data_map:
            if value.search(_content):
                yield key, value.findall(_content)

    def check_has_backlinks(self) -> None:
        """Check has backlinks in the content."""
        self.node.has_backlinks = not LogseqFile._BACKLINK_CRITERIA.isdisjoint(self.data.keys())
