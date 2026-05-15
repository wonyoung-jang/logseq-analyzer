"""Domain model classes for Logseq graph and files."""

import logging
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import unquote

from logseq_analyzer.utils.enums import BACKLINK_CRITERIA, Core, Crit, FileType, Output, TargetDir
from logseq_analyzer.utils.patterns import MASK_MAP, PATTERNS, PRIMARY_DATA_MAP, RAW_DATA_MAP, ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

logger = logging.getLogger(__name__)

BUILT_IN_PROPERTIES: frozenset[str] = frozenset(
    (
        "alias",
        "aliases",
        "background_color",
        "background-color",
        "collapsed",
        "created_at",
        "created-at",
        "custom-id",
        "doing",
        "done",
        "exclude-from-graph-view",
        "filetags",
        "filters",
        "heading",
        "hl-color",
        "hl-page",
        "hl-stamp",
        "hl-type",
        "icon",
        "id",
        "last_modified_at",
        "last-modified-at",
        "later",
        "logseq.color",
        "logseq.macro-arguments",
        "logseq.macro-name",
        "logseq.order-list-type",
        "logseq.query/nlp-date",
        "logseq.table.borders",
        "logseq.table.compact",
        "logseq.table.headers",
        "logseq.table.hover",
        "logseq.table.max-width",
        "logseq.table.stripes",
        "logseq.table.version",
        "logseq.tldraw.page",
        "logseq.tldraw.shape",
        "ls-type",
        "macro",
        "now",
        "public",
        "query-properties",
        "query-sort-by",
        "query-sort-desc",
        "query-table",
        "tags",
        "template-including-parent",
        "template",
        "title",
        "todo",
        "updated-at",
    )
)
_SIZE_UNITS: Sequence[str] = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
_ORDINAL_SUFFIX: dict[int, str] = {1: "st", 2: "nd", 3: "rd"}


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


def _format_bytes(size: int) -> str:
    """Convert a byte value into a human-readable string using IEC units.

    Args:
        size (int): Number of bytes.

    Returns:
        str: Human-readable string, e.g. '1.23 MB'.

    """
    if size < 0:
        msg = "size must be non-negative"
        raise ValueError(msg)
    if size < 1024:
        return f"{size} {_SIZE_UNITS[0]}"
    idx = min(int(math.log(size, 1024)), len(_SIZE_UNITS) - 1)
    return f"{size / 1024**idx:.2f} {_SIZE_UNITS[idx]}"


@dataclass(slots=True)
class FileIndex:
    """Class to index files in the Logseq graph."""

    _files: set[LogseqFile] = field(default_factory=set)
    _name_to_files: dict[str, list[LogseqFile]] = field(default_factory=lambda: defaultdict(list))

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
        msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile | str"
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
        msg = f"Invalid key type: {type(f).__name__}. Expected LogseqFile | str"
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
            if f.node.backlinked == backlinked and f.filetype == FileType.ASSET:
                yield f

    @property
    def report(self) -> dict:
        """Generate a report of the indexed files."""
        return {
            Output.Dir.INDEX: {
                Output.File.IDX_FILES: self._files,
                Output.File.IDX_NAME_TO_FILES: self._name_to_files,
            }
        }


@dataclass(slots=True)
class NodeType:
    """Class to hold node type data."""

    has_content: bool = False  # TODO: "mutable"
    has_backlinks: bool = False  # TODO: "mutable"
    backlinked: bool = False  # TODO: "mutable"
    backlinked_ns_only: bool = False  # TODO: "mutable"
    nodetype: str = Node.OTHER  # TODO: "mutable"

    def mark_backlinked(self) -> None:
        """Mark this node as backlinked."""
        self.backlinked = True
        self.backlinked_ns_only = False

    def mark_backlinked_ns_only(self) -> None:
        """Mark this node as backlinked via namespace only."""
        self.backlinked = False
        self.backlinked_ns_only = True

    def determine(self) -> None:
        """Determine node type based on summary data."""
        match (self.has_backlinks, self.backlinked, self.backlinked_ns_only):
            case (True, True, True) | (True, True, False) | (True, False, True):
                self.nodetype = Node.BRANCH
            case (True, False, False):
                self.nodetype = Node.ROOT
            case (False, True, True) | (False, True, False):
                self.nodetype = Node.LEAF
            case (False, False, True):
                self.nodetype = Node.ORPHAN_NAMESPACE if self.has_content else Node.ORPHAN_NAMESPACE_TRUE
            case (False, False, False):
                self.nodetype = Node.ORPHAN_GRAPH if self.has_content else Node.ORPHAN_TRUE


@dataclass(slots=True)
class LogseqFileContext:
    """Class to hold context data for a Logseq file."""

    now_ts: float
    journal_format: JournalFormats
    ns_file_sep: str
    graph_path: Path
    target: dict


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
    is_namespace: bool  # TODO: "mutable"
    children: set[str] = field(default_factory=set)  # TODO: "mutable"

    def mark_as_namespace_root(self) -> None:
        """Mark this page as a namespace root (does not contain NS_SEP itself)."""
        self.is_namespace = True

    def add_child(self, name: str) -> None:
        """Register a child namespace page."""
        self.children.add(name)

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
    ctx: LogseqFileContext = field(repr=False)
    name: str = field(init=False)
    content: str = field(init=False, repr=False)
    data: dict[str, Iterable[str]] = field(default_factory=dict, repr=False)
    filetype: str = field(init=False)
    primary_bullet: str = field(init=False, repr=False, default="")
    all_bullets: list[str] = field(default_factory=list, repr=False)
    node: NodeType = field(default_factory=NodeType, repr=False)
    _ns_info: NamespaceInfo | None = field(default=None, repr=False)
    _bullet_info: BulletInfo | None = field(default=None, repr=False)
    _file_info: FileInfo | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqFile object."""
        try:
            self.content = self.path.read_text(encoding="utf-8")
        except OSError, ValueError:
            self.content = ""
        self.name = self._get_name()
        self.filetype = self._get_filetype()
        if self.content:
            for i, bullet in self._iter_pattern_split():
                self.all_bullets.append(bullet)
                if bullet and i == 0:
                    self.primary_bullet = bullet
        if self.file_info.has_content:
            self.data.update(self._extract_primary_data())
            self.data.update(self._extract_aliases_and_propvalues())
            self.data.update(self._extract_properties())
            self.data.update(self._extract_patterns())
            self.node.has_content = bool(self.content)
            self.node.has_backlinks = not BACKLINK_CRITERIA.isdisjoint(self.data.keys())

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
        target_segment = uri_path.parts[len(uri_path.parts) - len(self.ctx.graph_path.parts)]
        target_segments_to_final = target_segment[:-1]
        if target_segments_to_final not in ("page", "block-id"):
            return ""
        graph_path = str(self.ctx.graph_path).replace("\\", "/")
        prefix = f"file:///{graph_path}/{target_segment}/"
        if not self.uri.startswith(prefix):
            logger.warning("URI does not start with the expected prefix: %s", prefix)
            return ""
        encoded_path = self.uri[len(prefix) : -(len(uri_path.suffix))].replace("___", "%2F").replace("%253A", "%3A")
        return f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"

    @property
    def file_info(self) -> FileInfo:
        """Return the information of the file."""
        if self._file_info is None:
            _stat = self.path.stat()
            self._file_info = FileInfo(
                time_existed=self.ctx.now_ts - _stat.st_birthtime,
                time_unmodified=self.ctx.now_ts - _stat.st_mtime,
                date_created=datetime.fromtimestamp(_stat.st_birthtime, tz=UTC).isoformat(),
                date_modified=datetime.fromtimestamp(_stat.st_mtime, tz=UTC).isoformat(),
                size=_stat.st_size,
                human_readable_size=_format_bytes(_stat.st_size),
                has_content=bool(_stat.st_size),
            )
        return self._file_info

    @property
    def ns_info(self) -> NamespaceInfo:
        """Return the namespace information of the file."""
        if self._ns_info is None:
            _ns_parts = self.name.split(Core.NS_SEP)
            self._ns_info = NamespaceInfo(
                parent_full=Core.NS_SEP.join(_ns_parts[:-1]),
                parent=_ns_parts[-2] if len(_ns_parts) > 2 else _ns_parts[0],
                parts=tuple((part, level) for level, part in enumerate(_ns_parts, start=1)),
                root=_ns_parts[0],
                is_namespace=Core.NS_SEP in self.name,
            )
        return self._ns_info

    @property
    def bullet_info(self) -> BulletInfo:
        """Return the bullet information of the file."""
        if self._bullet_info is None:
            self._bullet_info = BulletInfo(
                chars=len(self.content),
                bullets=len(self.all_bullets),
                empty_bullets=self.all_bullets.count(""),
            )
        return self._bullet_info

    def yield_linkedrefs(self) -> Iterator[str]:
        """Yield linked references from the file."""
        yield from chain(
            self.get_data(Crit.Content.ALIASES),
            self.get_data(Crit.Content.DRAW),
            self.get_data(Crit.Content.PAGE_REF),
            self.get_data(Crit.Content.TAG),
            self.get_data(Crit.Content.TAGGED_BACKLINK),
            self.get_data(Crit.Prop.PAGE_BUILTIN),
            self.get_data(Crit.Prop.PAGE_USER),
            self.get_data(Crit.Prop.BLOCK_BUILTIN),
            self.get_data(Crit.Prop.BLOCK_USER),
        )

    def yield_asset_mentions(self) -> Iterator[str]:
        """Yield asset mentions from the file."""
        yield from chain(
            self.get_data(Crit.Content.ASSETS),
            self.get_data(Crit.Emb.ASSET),
        )

    def yield_hls_bullet(self) -> Iterator[str]:
        """Yield HLS bullets from the file."""
        for bullet in self.all_bullets:
            if not bullet.strip().startswith("[:span]"):
                continue
            hl_page, id_, hl_stamp = "", "", ""
            for propvalue in ContentPatterns.PROPERTY_VALUE.finditer(bullet):
                key = propvalue.group(1)
                val = propvalue.group(2).strip()
                match key:
                    case "hl-page":
                        hl_page = val
                    case "id":
                        id_ = val
                    case "hl-stamp":
                        hl_stamp = val
            if all((hl_page, id_, hl_stamp)):
                yield f"{hl_page}_{id_}_{hl_stamp}"

    def get_data(self, key: str) -> Iterable[str]:
        """Get data by key."""
        return self.data.get(key, ())

    def set_filetype(self, filetype: str) -> None:
        """Set the file type of the file."""
        self.filetype = filetype

    def set_nodetype(self) -> None:
        """Determine the node type of the file."""
        if self.filetype in (FileType.JOURNAL, FileType.PAGE):
            self.node.determine()

    def _get_name(self) -> str:
        """Process the filename to create a page title."""
        name = self.path.stem.strip(self.ctx.ns_file_sep)
        if self.path.parent.name == self.ctx.target[TargetDir.JOURNAL][0]:
            try:
                date_obj = datetime.strptime(name, self.ctx.journal_format.file).replace(tzinfo=UTC)
                page_title = date_obj.strftime(self.ctx.journal_format.page)
                if Core.DATE_ORDINAL_SUFFIX in self.ctx.journal_format.page_title:
                    day_number = str(date_obj.day)
                    day_with_ordinal = _append_ordinal_to_day(day_number)
                    page_title = page_title.replace(day_number, day_with_ordinal, 1)
                return page_title.replace("'", "")
            except ValueError as e:
                logger.warning("Failed to parse date, key '%s', fmt `%s`: %s", name, self.ctx.journal_format.page, e)
                return name
        return unquote(name).replace(self.ctx.ns_file_sep, Core.NS_SEP)

    def _get_filetype(self) -> str:
        """Determine the file type based on the directory structure."""
        if _result := self.ctx.target.get(self.path.parent.name):
            return _result[1]
        for k, v in self.ctx.target.items():
            if k in self.path.parts:
                return v[2]
        return FileType.OTHER

    def _extract_primary_data(self) -> Iterator[tuple[str, Iterable[str]]]:
        """Extract primary data from the content."""
        masked = self.content
        for prefix, regex in MASK_MAP.items():
            masked = regex.sub(f"__{prefix}__{uuid.uuid4()}__", masked)
        for prefix, regex in PRIMARY_DATA_MAP.items():
            if result := regex.findall(masked):
                yield prefix, result
        for prefix, regex in RAW_DATA_MAP.items():
            if result := regex.findall(self.content):
                yield prefix, result

    def _extract_properties(self) -> Iterator[tuple[str, Iterable[str]]]:
        """Extract page and block properties from the content."""
        page_props = set()
        block_props = set()
        if self.primary_bullet and not self.primary_bullet.startswith("#"):
            page_props.update(ContentPatterns.PROPERTY.findall(self.primary_bullet))
            block_props.update(ContentPatterns.PROPERTY.findall("\n".join(self.all_bullets[1:])))
        else:
            block_props.update(ContentPatterns.PROPERTY.findall(self.content))
        if block_builtin := block_props.intersection(BUILT_IN_PROPERTIES):
            yield Crit.Prop.BLOCK_BUILTIN, block_builtin
        if block_user := block_props.difference(BUILT_IN_PROPERTIES):
            yield Crit.Prop.BLOCK_USER, block_user
        if page_builtin := page_props.intersection(BUILT_IN_PROPERTIES):
            yield Crit.Prop.PAGE_BUILTIN, page_builtin
        if page_user := page_props.difference(BUILT_IN_PROPERTIES):
            yield Crit.Prop.PAGE_USER, page_user

    def _extract_aliases_and_propvalues(self) -> Iterator[tuple[str, Iterable[str]]]:
        """Extract aliases and properties from the content."""
        if propvalues := dict(ContentPatterns.PROPERTY_VALUE.findall(self.content)):
            yield Crit.Prop.VALUES, propvalues
            alias_raw = propvalues.get("alias", "")
            alias = list(_process_aliases(alias_raw)) if alias_raw else []
            if alias:
                yield Crit.Content.ALIASES, alias

    def _extract_patterns(self) -> Iterator[tuple[str, Iterable[str]]]:
        """Process patterns in the content."""
        _temp_map = defaultdict(list)
        for ptn_cls in PATTERNS:
            for k, v in ptn_cls.process_hierarchy(self.content):
                _temp_map[k].append(v)
        yield from _temp_map.items()

    def _iter_pattern_split(self) -> Iterator[tuple[int, str]]:
        """Emulate re.Pattern.split() but yields sections of text instead of returning a list.

        Iterate over sections of text separated by bullet markers.

        Yields:
            Iterator[tuple[int, str]]: Sections of text with their respective indices.

        """
        count = 0
        iterator = ContentPatterns.BULLET.finditer(self.content)
        try:
            current = next(iterator)
        except StopIteration:
            yield count, self.content.strip("\t \n")
            return
        yield count, self.content[: current.start()].strip("\t \n")
        count += 1
        for nxt in iterator:
            yield count, self.content[current.end() : nxt.start()].strip("\t \n")
            count += 1
            current = nxt
        yield count, self.content[current.end() :].strip("\t \n")
