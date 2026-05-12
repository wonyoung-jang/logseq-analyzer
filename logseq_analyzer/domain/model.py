"""LogseqFile class to process Logseq files."""

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from logseq_analyzer.utils.enums import Core, Crit, FileType, Output, OutputDir
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES
from logseq_analyzer.utils.patterns import MASK_MAP, PATTERNS, PRIMARY_DATA_MAP, RAW_DATA_MAP, ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FileIndex:
    """Class to index files in the Logseq graph."""

    _files: set[LogseqFile] = field(default_factory=set)
    _name_to_files: dict[str, list[LogseqFile]] = field(default_factory=lambda: defaultdict(list))
    write_graph: bool = field(init=False, default=False)

    def __len__(self) -> int:
        """Return the number of files in the index."""
        return len(self._files)

    def __iter__(self) -> Iterator[LogseqFile]:
        """Iterate over the files in the index."""
        return iter(self._files)

    def __contains__(self, f: LogseqFile | str | object) -> bool:
        """Check if a file is in the index."""
        if isinstance(f, LogseqFile):
            return f in self._files
        if isinstance(f, str):
            return f in self._name_to_files
        msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path."
        raise TypeError(msg)

    def get_from_name(self, name: str) -> list[LogseqFile]:
        """Get files by their name."""
        return self._name_to_files.get(name, [])

    def add(self, f: LogseqFile) -> None:
        """Add a file to the index."""
        self._files.add(f)
        self._name_to_files[f.name].append(f)

    def remove(self, f: LogseqFile | str | object) -> None:
        """Strategy to remove a file from the index."""
        if isinstance(f, LogseqFile):
            target = f
            self._remove_file(target)
            logger.debug("Key %s removed from index.", f)
            return
        if isinstance(f, str):
            for target in self._name_to_files.pop(f, []):
                self._remove_file(target)
            return
        msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile, int, str, or Path."
        raise TypeError(msg)

    def _remove_file(self, f: LogseqFile) -> None:
        """Remove a file from the index."""
        self._files.discard(f)
        if files := self._name_to_files.get(f.name):
            try:
                files.remove(f)
            except ValueError:
                logger.warning("File %s not found in name_to_files list for name %s.", f, f.name)
        else:
            del self._name_to_files[f.name]

    def remove_deleted_files(self) -> None:
        """Remove deleted files from the cache."""
        if not self:
            return
        for f in self:
            if not f.path.exists():
                self.remove(f)

    def yield_names(self) -> Iterator[str]:
        """Yield all file names from the index."""
        yield from (f.name for f in self)

    def yield_non_ns_names(self) -> Iterator[str]:
        """Yield all non-namespace file names from the index."""
        yield from (f.name for f in self if not f.ns_info.is_namespace)

    def yield_journals(self) -> Iterator[str]:
        """Yield all journal files from the index."""
        yield from (f.name for f in self if f.filetype == FileType.JOURNAL)

    def yield_backlinked_assets(self, *, backlinked: bool) -> Iterator[LogseqFile]:
        """Yield asset files with or without backlinks."""
        for f in self:
            if (f.node.backlinked == backlinked or backlinked) and f.filetype == FileType.ASSET:
                yield f

    def yield_backlinked_assets_name(self, *, backlinked: bool) -> Iterator[str]:
        """Yield asset file names with or without backlinks."""
        for f in self:
            if (f.node.backlinked == backlinked or backlinked) and f.filetype == FileType.ASSET:
                yield f.name

    @property
    def graph_data(self) -> dict[LogseqFile, dict[str, Iterable[str]]]:
        """Get content data from the graph."""
        return {file: {k: v for k, v in file.data.items() if v} for file in self}

    @property
    def report(self) -> dict:
        """Generate a report of the indexed files."""
        _report: dict[str, object] = {
            Output.GRAPH_DATA: self.graph_data,
            Output.IDX_FILES: self._files,
            Output.IDX_NAME_TO_FILES: self._name_to_files,
        }
        if self.write_graph:
            _report[Output.GRAPH_CONTENT] = {f: f.content for f in self}
            _report[Output.GRAPH_BULLETS] = {f: f.all_bullets for f in self}
        return {OutputDir.INDEX: _report}


_BACKLINK_CRITERIA: frozenset[str] = frozenset(
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
_SI_UNITS: Sequence[str] = ("B", "kB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
_IEC_UNITS: Sequence[str] = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
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


def _process_aliases(aliases: str) -> Iterator[str]:
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


def _append_ordinal_to_day(day: str) -> str:
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    day_int = int(day)
    if 11 <= day_int <= 13:
        return day + "th"
    return day + _ORDINAL_SUFFIX.get(day_int % 10, "th")


def _process_filename(file: Path, ns_file_sep: str, journal_dir: str, jf: JournalFormats) -> str:
    """Process the filename to create a page title."""
    name = file.stem.strip(ns_file_sep)
    if file.parent.name == journal_dir:
        try:
            date_obj = datetime.strptime(name, jf.file).replace(tzinfo=UTC)
            page_title = date_obj.strftime(jf.page)
            if Core.DATE_ORDINAL_SUFFIX in jf.page_title:
                day_number = str(date_obj.day)
                day_with_ordinal = _append_ordinal_to_day(day_number)
                page_title = page_title.replace(day_number, day_with_ordinal, 1)
            return page_title.replace("'", "")
        except ValueError as e:
            logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, jf.page, e)
            return name
    return unquote(name).replace(ns_file_sep, Core.NS_SEP)


def _format_bytes(size: int, system: str = SizeUnit.SI, precision: int = 2) -> str:
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
    if system == SizeUnit.IEC:
        units, base = _IEC_UNITS, 1024
    elif system == SizeUnit.SI:
        units, base = _SI_UNITS, 1000
    else:
        msg = f"Invalid system '{system}'. Use 'si' or 'iec'."
        raise ValueError(msg)
    if size < base:
        return f"{size} {units[0]}"
    idx = 0
    _size = float(size)
    while _size >= base and idx < len(units) - 1:
        _size /= base
        idx += 1
    return f"{_size:.{precision}f} {units[idx]}"


@dataclass(slots=True)
class NodeType:
    """Class to hold node type data."""

    has_backlinks: bool = False
    backlinked: bool = False
    backlinked_ns_only: bool = False
    nodetype: str = Node.OTHER

    def determine_node_type(self, *, has_content: bool) -> None:
        """Determine node type based on summary data."""
        match (self.has_backlinks, self.backlinked, self.backlinked_ns_only):
            case (True, True, True) | (True, True, False) | (True, False, True):
                self.nodetype = Node.BRANCH
            case (True, False, False):
                self.nodetype = Node.ROOT
            case (False, True, True) | (False, True, False):
                self.nodetype = Node.LEAF
            case (False, False, True):
                self.nodetype = Node.ORPHAN_NAMESPACE if has_content else Node.ORPHAN_NAMESPACE_TRUE
            case (False, False, False):
                self.nodetype = Node.ORPHAN_GRAPH if has_content else Node.ORPHAN_TRUE


@dataclass(slots=True)
class LogseqFileContext:
    """Class to hold context data for a Logseq file."""

    now_ts: float
    journal_format: JournalFormats
    ns_file_sep: str
    journal_dir: str
    graph_path: Path
    filetype_map: dict


@dataclass(slots=True)
class JournalFormats:
    """Formats for Logseq journal files and pages."""

    file: str
    page: str
    page_title: str


@dataclass(slots=True)
class FileInfo:
    """File timestamp information class."""

    time_existed: float
    time_unmodified: float
    date_created: str
    date_modified: str
    size: int
    human_readable_size: str
    has_content: bool


@dataclass(slots=True)
class NamespaceInfo:
    """NamespaceInfo class."""

    parent_full: str
    parent: str
    parts: tuple[tuple[str, int], ...]
    root: str
    stem: str
    is_namespace: bool
    children: set[str] = field(default_factory=set)

    @property
    def size(self) -> int:
        """Return the number of parts in the namespace."""
        return len(self.children)


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
class LogseqFile:
    """A class to represent a Logseq file."""

    path: Path
    context: LogseqFileContext = field(repr=False)
    name: str = field(init=False)
    content: str = field(init=False, repr=False)
    data: dict[str, Iterable[str]] = field(default_factory=dict, repr=False)
    filetype: str = field(init=False)
    primary_bullet: str = field(init=False, repr=False, default="")
    all_bullets: list[str] = field(default_factory=list, repr=False)
    node: NodeType = field(default_factory=NodeType, repr=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqFile object."""
        try:
            self.content = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Failed to decode file %s with utf-8 encoding.", self.path)
            self.content = ""
        self.name = _process_filename(
            self.path,
            jf=self.context.journal_format,
            ns_file_sep=self.context.ns_file_sep,
            journal_dir=self.context.journal_dir,
        )
        self.filetype = self.evaluate_file_type()
        if self.content:
            for i, bullet in self._iter_pattern_split():
                self.all_bullets.append(bullet)
                if bullet and i == 0:
                    self.primary_bullet = bullet
        if self.file_info.has_content:
            self.data.update(self.extract_primary_data())
            self.data.update(self.extract_aliases_and_propvalues())
            self.data.update(self.extract_properties())
            self.data.update(self.extract_patterns())
            self.node.has_backlinks = not _BACKLINK_CRITERIA.isdisjoint(self.data.keys())

    def __hash__(self) -> int:
        """Return the hash of the LogseqFile based on its path."""
        return hash(self.path.parts)

    def __eq__(self, other: object) -> bool:
        """Check equality based on the file path."""
        if isinstance(other, LogseqFile):
            return self.path.parts == other.path.parts
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        """Compare LogseqFile objects based on their file names."""
        if isinstance(other, LogseqFile):
            return self.name < other.name
        if isinstance(other, str):
            return self.name < other
        return NotImplemented

    @property
    def is_hls(self) -> bool:
        """Check if the file is an HLS asset."""
        return self.name.startswith(Core.HLS_PREFIX)

    @property
    def uri(self) -> str:
        """Return the file URI."""
        return self.path.as_uri()

    @property
    def ls_url(self) -> str:
        """Return the Logseq URL."""
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

    @property
    def file_info(self) -> FileInfo:
        """Return the information of the file."""
        _stat = self.path.stat()
        return FileInfo(
            time_existed=self.context.now_ts - _stat.st_birthtime,
            time_unmodified=self.context.now_ts - _stat.st_mtime,
            date_created=datetime.fromtimestamp(_stat.st_birthtime, tz=UTC).isoformat(),
            date_modified=datetime.fromtimestamp(_stat.st_mtime, tz=UTC).isoformat(),
            size=_stat.st_size,
            human_readable_size=_format_bytes(_stat.st_size),
            has_content=bool(_stat.st_size),
        )

    @property
    def ns_info(self) -> NamespaceInfo:
        """Return the namespace information of the file."""
        _ns_parts = self.name.split(Core.NS_SEP)
        return NamespaceInfo(
            parts=tuple((part, level) for level, part in enumerate(_ns_parts, start=1)),
            root=_ns_parts[0],
            parent=_ns_parts[-2] if len(_ns_parts) > 2 else _ns_parts[0],
            parent_full=Core.NS_SEP.join(_ns_parts[:-1]),
            stem=_ns_parts[-1],
            is_namespace=Core.NS_SEP in self.name,
        )

    @property
    def bullet_info(self) -> BulletInfo:
        """Return the bullet information of the file."""
        return BulletInfo(
            chars=len(self.content),
            bullets=len(self.all_bullets),
            empty_bullets=self.all_bullets.count(""),
        )

    def evaluate_file_type(self) -> str:
        """Determine the file type based on the directory structure."""
        if (_result := self.context.filetype_map.get(self.path.parent.name)) and _result[0] != FileType.OTHER:
            return _result[0]
        for key, _result in self.context.filetype_map.items():
            if key in self.path.parts:
                return _result[1]
        return FileType.OTHER

    def extract_primary_data(self) -> Iterator[tuple[str, list[str]]]:
        """Extract primary data from the content."""
        _masked_content = self.content
        for prefix, regex in MASK_MAP.items():
            _masked_content = regex.sub(f"__{prefix}__{uuid.uuid4()}__", _masked_content)
        for prefix, regex in PRIMARY_DATA_MAP.items():
            if regex.search(_masked_content):
                yield prefix, regex.findall(_masked_content)
        for prefix, regex in RAW_DATA_MAP.items():
            if regex.search(self.content):
                yield prefix, regex.findall(self.content)

    def extract_properties(self) -> Iterator[tuple[str, set[str]]]:
        """Extract page and block properties from the content."""
        page_props = set()
        if self.primary_bullet and not self.primary_bullet.startswith("#"):
            page_props.update(ContentPatterns.PROPERTY.findall(self.primary_bullet))
            self.content = "\n".join(self.all_bullets)
        block_props = set(ContentPatterns.PROPERTY.findall(self.content))
        if block_builtin := block_props.intersection(BUILT_IN_PROPERTIES):
            yield Crit.Prop.BLOCK_BUILTIN, block_builtin
        if block_user := block_props.difference(BUILT_IN_PROPERTIES):
            yield Crit.Prop.BLOCK_USER, block_user
        if page_builtin := page_props.intersection(BUILT_IN_PROPERTIES):
            yield Crit.Prop.PAGE_BUILTIN, page_builtin
        if page_user := page_props.difference(BUILT_IN_PROPERTIES):
            yield Crit.Prop.PAGE_USER, page_user

    def extract_aliases_and_propvalues(self) -> Iterator[tuple[str, list[str] | dict[str, str]]]:
        """Extract aliases and properties from the content."""
        propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(self.content))
        if propvalues:
            yield Crit.Prop.VALUES, propvalues
        aliases = list(_process_aliases(raw)) if (raw := propvalues.get("alias")) else []
        if aliases:
            yield Crit.Content.ALIASES, aliases

    def extract_patterns(self) -> Iterator[tuple[str, list[str]]]:
        """Process patterns in the content."""
        _temp_map = defaultdict(list)
        for ptn_cls in PATTERNS:
            for k, v in ptn_cls.process_pattern_hierarchy(self.content):
                _temp_map[k].append(v)
        yield from _temp_map.items()

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
