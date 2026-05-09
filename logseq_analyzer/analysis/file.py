"""LogseqFile class to process Logseq files."""

import logging
import uuid
from collections import defaultdict
from dataclasses import InitVar, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from logseq_analyzer.utils.enums import Core, Crit, FileType
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES
from logseq_analyzer.utils.patterns import MASK_MAP, PATTERNS, PRIMARY_DATA_MAP, RAW_DATA_MAP, ContentPatterns

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator, Sequence
    from os import stat_result

logger = logging.getLogger(__name__)

BACKLINK_CRITERIA: frozenset[str] = frozenset(
    (
        Crit.Prop.VALUES,
        Crit.Prop.BLOCK_BUILTIN,
        Crit.Prop.BLOCK_USER,
        Crit.Prop.PAGE_BUILTIN,
        Crit.Prop.PAGE_USER,
        Crit.Content.PAGE_REF,
        Crit.Content.TAGGED_BACKLINK,
        Crit.Content.TAG,
    )
)
SI_UNITS: Sequence[str] = ("B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
IEC_UNITS: Sequence[str] = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
_ORDINAL_SUFFIX: dict[int, str] = {1: "st", 2: "nd", 3: "rd"}


class SizeUnit(StrEnum):
    """Enumeration for size units."""

    SI = "si"  # Powers of 1000
    IEC = "iec"  # Powers of 1024


class Node(StrEnum):
    """Node types for the Logseq Analyzer."""

    BRANCH = "branch"
    LEAF = "leaf"
    ORPHAN_GRAPH = "orphan_graph"
    ORPHAN_NAMESPACE = "orphan_namespace"
    ORPHAN_NAMESPACE_TRUE = "orphan_namespace_true"
    ORPHAN_TRUE = "orphan_true"
    OTHER = "other"
    ROOT = "root"


def process_aliases(aliases: str) -> Iterator[str]:
    """Process aliases to extract individual aliases."""
    if not (aliases := aliases.strip()):
        return
    current = []
    is_inside_brackets = False
    pos = 0
    while pos < len(aliases):
        if aliases[pos : pos + 2] == "[[":
            is_inside_brackets = True
            pos += 2
        elif aliases[pos : pos + 2] == "]]":
            is_inside_brackets = False
            pos += 2
        elif aliases[pos] == "," and not is_inside_brackets:
            if part := "".join(current).strip().lower():
                yield part
            current.clear()
            pos += 1
        else:
            current.append(aliases[pos])
            pos += 1
    if part := "".join(current).strip().lower():
        yield part


@dataclass(slots=True)
class LogseqBullets:
    """LogseqBullets class."""

    content: str
    all_bullets: list[str] = field(default_factory=list)
    primary: str = ""

    def __post_init__(self) -> None:
        """Process the content to extract bullet information."""
        if self.content:
            for bullet_index, bullet in self._iter_pattern_split():
                self.all_bullets.append(bullet)
                if bullet and bullet_index == 0:
                    self.primary = bullet

    def _iter_pattern_split(self, maxsplit: int = 0) -> Iterator[tuple[int, str]]:
        """Emulate re.Pattern.split() but yields sections of text instead of returning a list.

        Iterate over sections of text separated by bullet markers.

        Args:
            maxsplit (int): Maximum number of splits. If 0, all sections are returned.

        Yields:
            Iterator[tuple[int, str]]: Sections of text with their respective indices.

        """
        _count = 0
        for match in ContentPatterns.BULLET.finditer(self.content):
            if maxsplit and _count >= maxsplit:
                break
            if _count == 0:
                yield _count, self.content[: match.start()].strip("\t \n")
                _count += 1
            content_start = match.end()
            next_match = next(ContentPatterns.BULLET.finditer(self.content, content_start), None)
            content_end = next_match.start() if next_match else len(self.content)
            yield _count, self.content[content_start:content_end].strip("\t \n")
            _count += 1
        if _count == 0:
            yield _count, self.content.strip("\t \n")

    @property
    def bullet_info(self) -> BulletInfo:
        """Get bullet statistics."""
        return BulletInfo(
            chars=len(self.content),
            bullets=len(self.all_bullets),
            empty_bullets=self.all_bullets.count(""),
        )

    def extract_primary_raw_data(self) -> Iterator[tuple[str, Any]]:
        """Extract primary data from the content."""
        for key, value in RAW_DATA_MAP.items():
            if value.search(self.content):
                yield key, value.findall(self.content)

    def extract_properties(self) -> Iterator[tuple[str, Any]]:
        """Extract page and block properties from the content."""
        page_props = set()
        if self.primary and not self.primary.startswith("#"):
            page_props.update(ContentPatterns.PROPERTY.findall(self.primary))
            self.content = "\n".join(self.all_bullets)
        block_props = set(ContentPatterns.PROPERTY.findall(self.content))
        for key, value in {
            Crit.Prop.BLOCK_BUILTIN: block_props.intersection(BUILT_IN_PROPERTIES),
            Crit.Prop.BLOCK_USER: block_props.difference(BUILT_IN_PROPERTIES),
            Crit.Prop.PAGE_BUILTIN: page_props.intersection(BUILT_IN_PROPERTIES),
            Crit.Prop.PAGE_USER: page_props.difference(BUILT_IN_PROPERTIES),
        }.items():
            if value:
                yield key, value

    def extract_aliases_and_propvalues(self) -> Iterator[tuple[str, Any]]:
        """Extract aliases and properties from the content."""
        propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(self.content))
        aliases = list(process_aliases(raw)) if (raw := propvalues.get("alias")) else None
        for key, value in {
            Crit.Content.ALIASES: aliases,
            Crit.Prop.VALUES: propvalues,
        }.items():
            if value:
                yield key, value

    def extract_patterns(self) -> Iterator[tuple[str, list[str]]]:
        """Process patterns in the content."""
        _temp_map = defaultdict(list)
        for ptn_cls in PATTERNS:
            for k, v in ptn_cls.process_pattern_hierarchy(self.content):
                _temp_map[k].append(v)
        yield from _temp_map.items()


def _append_ordinal_to_day(day: str) -> str:
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    day_int = int(day)
    if 11 <= day_int <= 13:
        return day + "th"
    return day + _ORDINAL_SUFFIX.get(day_int % 10, "th")


def _get_non_journal_key(name: str, ns_file_sep: str) -> str:
    """Process non-journal keys to create a page title."""
    return unquote(name).replace(ns_file_sep, Core.NS_SEP)


def _get_journal_key(name: str, file_fmt: str, page_fmt: str, page_title_fmt: str) -> str:
    """Process the journal key to create a page title."""
    try:
        date_obj = datetime.strptime(name, file_fmt).replace(tzinfo=UTC)
        page_title = date_obj.strftime(page_fmt)
        if Core.DATE_ORDINAL_SUFFIX in page_title_fmt:
            day_number = str(date_obj.day)
            day_with_ordinal = _append_ordinal_to_day(day_number)
            page_title = page_title.replace(day_number, day_with_ordinal, 1)
        return page_title.replace("'", "")
    except ValueError as e:
        logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, page_fmt, e)
        return name


def _process_filename(file: Path, ns_file_sep: str, journal_dir: str, jf: JournalFormats) -> str:
    """Process the filename to create a page title."""
    name = file.stem.strip(ns_file_sep)
    if file.parent.name == journal_dir:
        return _get_journal_key(name, jf.file, jf.page, jf.page_title)
    return _get_non_journal_key(name, ns_file_sep)


def format_bytes(size: int, system: str = SizeUnit.SI, precision: int = 2) -> str:
    """Convert a byte value into a human-readable string using SI or IEC units.

    Args:
        size (int): Number of bytes.
        system (str): 'si' for powers of 1000, 'iec' for powers of 1024.
        precision (int): Number of decimal places.

    Returns:
        str: Human-readable string, e.g. '1.23 MB' or '1.20 MiB'.

    """
    if size < 0:
        msg = "size_bytes must be non-negative"
        raise ValueError(msg)
    is_iec = system == SizeUnit.IEC
    units = IEC_UNITS if is_iec else SI_UNITS
    base = 1024 if is_iec else 1000
    if size < base:
        return f"{size} {units[0]}"
    idx = 0
    _size = float(size)
    while _size >= base and idx < len(units) - 1:
        _size /= base
        idx += 1
    return f"{_size:.{precision}f} {units[idx]}"


@dataclass(slots=True)
class LogseqPath:
    """LogseqPath class."""

    file: Path
    context: LogseqFileContext
    file_type: str = ""
    logseq_url: str = ""
    name: str = ""
    uri: str = field(init=False)
    _stat: stat_result = field(init=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqPath object."""
        self._stat = self.file.stat()
        self.uri = self.file.as_uri()
        self.name = _process_filename(
            self.file,
            jf=self.context.journal_format,
            ns_file_sep=self.context.ns_file_sep,
            journal_dir=self.context.journal_dir,
        )
        self.file_type = self.evaluate_file_type()
        self.logseq_url = self.set_logseq_url()

    def evaluate_file_type(self) -> str:
        """Determine the file type based on the directory structure."""
        if (_result := self.context.result_map.get(self.file.parent.name)) and _result[0] != FileType.OTHER:
            return _result[0]
        for key, _result in self.context.result_map.items():
            if key in self.file.parts:
                return _result[1]
        return FileType.OTHER

    def set_logseq_url(self) -> str:
        """Set the Logseq URL."""
        uri_path = Path(self.uri)
        target_segment = uri_path.parts[len(uri_path.parts) - len(self.context.graph_path.parts)]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            return ""
        graph_path = str(self.context.graph_path).replace("\\", "/")
        prefix = f"file:///{graph_path}/{target_segment}/"
        if not self.uri.startswith(prefix):
            logger.warning("URI does not start with the expected prefix: %s", prefix)
            return ""
        encoded_path = self.uri[len(prefix) : -(len(uri_path.suffix))].replace("___", "%2F").replace("%253A", "%3A")
        return f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"

    def read_text(self) -> str:
        """Read the text content of a file."""
        try:
            return self.file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Failed to decode file %s with utf-8 encoding.", self.file)
            return ""

    @property
    def timestamp_info(self) -> TimestampInfo:
        """Get the timestamps for the file."""
        return TimestampInfo(
            time_existed=self.context.now_ts - self._stat.st_birthtime,
            time_unmodified=self.context.now_ts - self._stat.st_mtime,
            date_created=datetime.fromtimestamp(self._stat.st_birthtime, tz=UTC).isoformat(),
            date_modified=datetime.fromtimestamp(self._stat.st_mtime, tz=UTC).isoformat(),
        )

    @property
    def size_info(self) -> SizeInfo:
        """Get the size information for the file."""
        return SizeInfo(
            size=self._stat.st_size,
            human_readable_size=format_bytes(self._stat.st_size),
            has_content=bool(self._stat.st_size),
        )

    @property
    def namespace_info(self) -> NamespaceInfo:
        """Get the namespace name data."""
        _ns_parts = self.name.split(Core.NS_SEP)
        return NamespaceInfo(
            parts={part: level for level, part in enumerate(_ns_parts, start=1)},
            root=_ns_parts[0],
            parent=_ns_parts[-2] if len(_ns_parts) > 2 else _ns_parts[0],
            parent_full=Core.NS_SEP.join(_ns_parts[:-1]),
            stem=_ns_parts[-1],
            is_namespace=Core.NS_SEP in self.name,
        )


@dataclass(slots=True)
class NodeType:
    """Class to hold node type data."""

    has_backlinks: bool = False
    backlinked: bool = False
    backlinked_ns_only: bool = False
    node_type: str = Node.OTHER

    def determine_node_type(self, *, has_content: bool) -> None:
        """Determine node type based on summary data."""
        match (self.has_backlinks, self.backlinked, self.backlinked_ns_only):
            case (True, True, True) | (True, True, False) | (True, False, True):
                self.node_type = Node.BRANCH
            case (True, False, False):
                self.node_type = Node.ROOT
            case (False, True, True) | (False, True, False):
                self.node_type = Node.LEAF
            case (False, False, True):
                self.node_type = Node.ORPHAN_NAMESPACE if has_content else Node.ORPHAN_NAMESPACE_TRUE
            case (False, False, False):
                self.node_type = Node.ORPHAN_GRAPH if has_content else Node.ORPHAN_TRUE


@dataclass(slots=True)
class LogseqFileContext:
    """Class to hold context data for a Logseq file."""

    now_ts: float
    journal_format: JournalFormats
    ns_file_sep: str
    journal_dir: str
    graph_path: Path
    result_map: dict


@dataclass(slots=True)
class JournalFormats:
    """Formats for Logseq journal files and pages."""

    file: str
    page: str
    page_title: str


@dataclass(slots=True)
class TimestampInfo:
    """File timestamp information class."""

    time_existed: float
    time_unmodified: float
    date_created: str
    date_modified: str


@dataclass(slots=True)
class SizeInfo:
    """File size information class."""

    size: int
    human_readable_size: str
    has_content: bool


@dataclass(slots=True)
class NamespaceInfo:
    """NamespaceInfo class."""

    parent_full: str
    parent: str
    parts: dict[str, int]
    root: str
    stem: str
    is_namespace: bool
    children: set[str] = field(default_factory=set)


@dataclass(slots=True)
class BulletInfo:
    """Bullet statistics class."""

    chars: int
    bullets: int
    empty_bullets: int
    char_per_bullet: float | None = field(init=False)

    def __post_init__(self) -> None:
        """Calculate characters per bullet."""
        self.char_per_bullet = round(self.chars / self.bullets, 2) if self.bullets else None


@dataclass(slots=True)
class LogseqFileInfo:
    """LogseqFileInfo class."""

    timestamp: TimestampInfo
    size: SizeInfo
    namespace: NamespaceInfo
    bullet: BulletInfo


@dataclass(slots=True)
class LogseqFile:
    """A class to represent a Logseq file."""

    path_input: InitVar[Path]
    context: LogseqFileContext = field(repr=False)
    data: dict[str, Any] = field(default_factory=dict)
    node: NodeType = field(default_factory=NodeType)
    is_hls: bool = False
    masked_content: str = ""
    masked_blocks: dict[str, str] = field(default_factory=dict)
    path: LogseqPath = field(init=False)
    bullets: LogseqBullets = field(init=False)
    info: LogseqFileInfo = field(init=False)

    def __post_init__(self, path_input: Path) -> None:
        """Initialize the LogseqFile object."""
        self.path = LogseqPath(
            file=path_input,
            context=self.context,
        )
        self.bullets = LogseqBullets(
            content=self.path.read_text(),
        )
        self.info = LogseqFileInfo(
            timestamp=self.path.timestamp_info,
            size=self.path.size_info,
            namespace=self.path.namespace_info,
            bullet=self.bullets.bullet_info,
        )
        self.is_hls = self.path.name.startswith(Core.HLS_PREFIX)
        if self.info.size.has_content:
            self.data.update(self.extract_primary_data())
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

    def extract_primary_data(self) -> Iterator[tuple[str, Any]]:
        """Extract primary data from the content."""
        self.masked_content = self.bullets.content

        for prefix, regex in MASK_MAP.items():

            def _repl(match: re.Match, prefix: str = prefix) -> str:
                placeholder = f"__{prefix}__{uuid.uuid4()}__"
                self.masked_blocks[placeholder] = match.group(0)
                return placeholder

            self.masked_content = regex.sub(_repl, self.masked_content)

        for key, value in PRIMARY_DATA_MAP.items():
            if value.search(self.masked_content):
                yield key, value.findall(self.masked_content)

    def unmask_blocks(self) -> None:
        """Restore the original content by replacing placeholders with their blocks."""
        for placeholder, block in self.masked_blocks.items():
            self.masked_content = self.masked_content.replace(placeholder, block)
