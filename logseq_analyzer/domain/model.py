"""Domain model classes for Logseq graph and files."""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import chain
from typing import TYPE_CHECKING

from logseq_analyzer.domain.enums import BACKLINK_CRITERIA, Core, Crit, FileType
from logseq_analyzer.domain.patterns import MASK_MAP, PATTERNS, PRIMARY_DATA_MAP, RAW_DATA_MAP, ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

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


_ALIAS_TOKEN = re.compile(r"\[\[([^\]]+?)]]|([^,\[\]]+)")


def _process_aliases(aliases: str) -> Iterator[str]:
    """Process aliases to extract individual aliases."""
    for m in _ALIAS_TOKEN.finditer(aliases):
        token = (m.group(1) or m.group(2)).strip().lower()
        if token:
            yield token


@dataclass(slots=True)
class FileIndex:
    """Class to index files in the Logseq graph."""

    file: set[LogseqFile] = field(default_factory=set)

    def __len__(self) -> int:
        """Return the number of files in the index."""
        return len(self.file)

    def __iter__(self) -> Iterator[LogseqFile]:
        """Iterate over the files in the index."""
        return iter(self.file)

    def add(self, f: LogseqFile) -> None:
        """Add a file to the index."""
        self.file.add(f)

    def update(self, files: Iterable[LogseqFile]) -> None:
        """Update the index with a set of files."""
        self.file.update(files)

    def yield_backlinked_assets(self, *, backlinked: bool) -> Iterator[LogseqFile]:
        """Yield asset files with or without backlinks."""
        yield from (f for f in self if f.node.backlinked == backlinked and f.filetype == FileType.ASSET)


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

    def mark_backlinked_ns(self) -> None:
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
class NamespaceInfo:
    """NamespaceInfo class.

    Some facts:
        If not is_namespace, then parent is ""
    """

    is_namespace: bool  # TODO: "mutable"
    root: str
    parent: str
    part: list[str]

    def __repr__(self) -> str:
        """Return a string representation of the NamespaceInfo."""
        return f"""
        NamespaceInfo(
            is_namespace={self.is_namespace},
            root='{self.root}',
            parent='{self.parent}',
            part={self.part},
        )
        """

    @classmethod
    def from_name(cls, name: str, sep: str = Core.NS_SEP) -> NamespaceInfo:
        is_namespace = sep in name
        part = name.split(sep)
        root = part[0] if is_namespace else ""
        parent = name.rsplit(sep, 1)[0] if is_namespace else ""
        return cls(is_namespace=is_namespace, root=root, parent=parent, part=part)

    def mark_as_namespace(self) -> None:
        self.is_namespace = True


@dataclass(slots=True)
class LogseqFile:
    """A class to represent a Logseq file."""

    path: Path
    content: str = field(repr=False)
    name: str
    filetype: str
    data: dict[str, Iterable[str]] = field(default_factory=dict, repr=False)
    node: NodeType = field(default_factory=NodeType, repr=False)
    is_hls: bool = field(init=False, repr=False)
    ns_info: NamespaceInfo = field(init=False, repr=False)
    _first_bullet: str = field(init=False, repr=False, default="")
    _bullet: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqFile object."""
        self.is_hls = self.name.startswith(Core.HLS_PREFIX)
        self.ns_info = NamespaceInfo.from_name(self.name)
        if self.content:
            self._bullet.extend(b.strip("\t \n") for b in ContentPatterns.BULLET.split(self.content))
            self._first_bullet = self._bullet[0] if self._bullet else ""
            self.data.update(self._extract_data())
            self.node.has_content = True
            self.node.has_backlinks = not BACKLINK_CRITERIA.isdisjoint(self.data.keys())

    def __hash__(self) -> int:
        """Return the hash of the LogseqFile based on its path."""
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        """Check equality based on the file path."""
        if isinstance(other, LogseqFile):
            return self.path == other.path
        return NotImplemented

    def __lt__(self, other: object) -> bool:
        """Compare LogseqFile objects based on their file names."""
        if isinstance(other, LogseqFile):
            return self.name < other.name
        return NotImplemented

    def yield_linkedrefs(self) -> Iterator[str]:
        """Yield linked references from the file."""
        yield from chain(
            self.get_data(Crit.Content.ALIAS),
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
            self.get_data(Crit.Content.ASSET),
            self.get_data(Crit.EmbLink.ASSET),
        )

    def parse_hls_bullet(self, bullet: str) -> str | None:
        """Parse the first bullet of an HLS file to extract the page name."""
        if not bullet.strip().startswith("[:span]"):
            return None
        props = {m.group(1): m.group(2).strip() for m in ContentPatterns.PROPERTY_VALUE.finditer(bullet)}
        hl_page = props.get("hl-page", "")
        id_ = props.get("id", "")
        hl_stamp = props.get("hl-stamp", "")
        if hl_page and id_ and hl_stamp:
            return f"{hl_page}_{id_}_{hl_stamp}"
        return None

    def yield_hls_bullet(self) -> Iterator[str]:
        """Yield HLS bullets from the file."""
        yield from filter(None, (self.parse_hls_bullet(b) for b in self._bullet))

    def get_data(self, key: str) -> Iterable[str]:
        """Get data by key."""
        return self.data.get(key, ())

    def _extract_data(self) -> Iterator[tuple[str, Iterable[str]]]:
        """Extract primary data and properties from the content."""
        yield from ((p, d) for p, d in self._extract() if d)

    def _extract(self) -> Iterator[tuple[str, Iterable[str]]]:
        """Extract aliases, and page and block properties from the content."""
        masked = self.content
        for prefix, regex in MASK_MAP.items():
            masked = regex.sub(f"__{prefix}__", masked)
        yield from ((p, r.findall(masked)) for p, r in PRIMARY_DATA_MAP.items())
        yield from ((p, r.findall(self.content)) for p, r in RAW_DATA_MAP.items())
        propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(self.content))
        yield Crit.Prop.VALUES, propvalues
        yield Crit.Content.ALIAS, list(_process_aliases(propvalues.get("alias", "")))
        if self._first_bullet and not self._first_bullet.startswith("#"):
            page_props = set(ContentPatterns.PROPERTY.findall(self._first_bullet))
            block_props = set(ContentPatterns.PROPERTY.findall("\n".join(self._bullet[1:])))
        else:
            page_props = set()
            block_props = set(propvalues.keys())
        yield Crit.Prop.BLOCK_BUILTIN, block_props.intersection(BUILT_IN_PROPERTIES)
        yield Crit.Prop.BLOCK_USER, block_props.difference(BUILT_IN_PROPERTIES)
        yield Crit.Prop.PAGE_BUILTIN, page_props.intersection(BUILT_IN_PROPERTIES)
        yield Crit.Prop.PAGE_USER, page_props.difference(BUILT_IN_PROPERTIES)
        data = defaultdict(list)
        for ptn in PATTERNS:
            for p, v in ptn.process_hierarchy(self.content):
                data[p].append(v)
        yield from data.items()


# def _ls_url(uri: str, graphpath: Path) -> str:  # TODO: Unused
#     """Return the Logseq URL."""
#     uri_path = Path(uri)
#     target_segment = uri_path.parts[len(uri_path.parts) - len(graphpath.parts)]
#     target_segments_to_final = target_segment[:-1]
#     if target_segments_to_final not in ("page", "block-id"):
#         return ""
#     graph_path = str(graphpath).replace("\\", "/")
#     prefix = f"file:///{graph_path}/{target_segment}/"
#     if not uri.startswith(prefix):
#         logger.warning("URI does not start with the expected prefix: %s", prefix)
#         return ""
#     encoded_path = uri[len(prefix) : -(len(uri_path.suffix))].replace("___", "%2F").replace("%253A", "%3A")
#     return f"logseq://graph/Logseq?{target_segments_to_final}={encoded_path}"
