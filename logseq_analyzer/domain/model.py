"""Domain model classes for Logseq graph and files."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import chain
from typing import TYPE_CHECKING

from logseq_analyzer.domain.enums import BACKLINK_CRITERIA, Core, Crit, FileType
from logseq_analyzer.domain.patterns import (
    CORE_PATTERN,
    HIERARCHICAL_PATTERN,
    MASK_PATTERN,
    RAW_PATTERN,
    ContentPatterns,
)

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


def _parse_hls_bullet(bullet: str) -> str | None:
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


def yield_asset(index: set[LogseqFile], *, link: bool) -> Iterator[LogseqFile]:
    """Yield asset files with or without backlinks."""
    yield from (f for f in index if f.backlinked == link and f.filetype == FileType.ASSET)


def get_content_data(content: str) -> tuple[dict[str, Iterable[str]], bool]:
    """Extract primary data and properties from the content."""
    data = {k: v for k, v in _extract(content) if v}
    has_backlinks = not BACKLINK_CRITERIA.isdisjoint(data.keys())
    return data, has_backlinks


def _extract(content: str) -> Iterator[tuple[str, Iterable[str]]]:
    """Extract all relevant data from the content."""
    masked = content
    for p, r in MASK_PATTERN:
        masked = r.sub(f"__{p}__", masked)
    yield from ((p, r.findall(masked)) for p, r in CORE_PATTERN)
    yield from ((p, r.findall(content)) for p, r in RAW_PATTERN)
    propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(content))
    yield Crit.Prop.VALUES, propvalues
    yield Crit.Content.ALIAS, list(_process_aliases(propvalues.get("alias", "")))
    bullet = [b.strip("\t \n") for b in ContentPatterns.BULLET.split(content)]
    first_bullet = bullet[0] if bullet else ""
    if first_bullet and not first_bullet.startswith("#"):
        page_props = set(ContentPatterns.PROPERTY.findall(first_bullet))
        block_props = set(ContentPatterns.PROPERTY.findall("\n".join(bullet[1:])))
    else:
        page_props = set()
        block_props = set(propvalues.keys())
    yield Crit.Prop.BLOCK_BUILTIN, block_props.intersection(BUILT_IN_PROPERTIES)
    yield Crit.Prop.BLOCK_USER, block_props.difference(BUILT_IN_PROPERTIES)
    yield Crit.Prop.PAGE_BUILTIN, page_props.intersection(BUILT_IN_PROPERTIES)
    yield Crit.Prop.PAGE_USER, page_props.difference(BUILT_IN_PROPERTIES)
    yield Crit.Content.HLS_BULLET, list(filter(None, (_parse_hls_bullet(b) for b in bullet)))
    data = defaultdict(list)
    for ptn in HIERARCHICAL_PATTERN:
        for p, v in ptn.process_hierarchy(content):
            data[p].append(v)
    yield from data.items()


@dataclass(slots=True)
class LogseqFile:
    """A class to represent a Logseq file."""

    path: Path
    name: str
    filetype: str
    data: dict[str, Iterable[str]] = field(repr=False)
    has_content: bool = field(default=False)
    has_backlinks: bool = field(default=False)

    is_hls: bool = field(init=False)
    is_ns: bool = field(init=False, default=False)
    ns_root: str = field(init=False)
    ns_parent: str = field(init=False)
    ns_part: list[str] = field(init=False)
    backlinked: bool = field(init=False, default=False)
    backlinked_ns_only: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        """Initialize the LogseqFile object."""
        self.is_hls = self.name.startswith(Core.HLS_PREFIX)
        self.is_ns = Core.NS_SEP in self.name
        self.ns_part = self.name.split(Core.NS_SEP)
        self.ns_root = self.ns_part[0] if self.is_ns else ""
        self.ns_parent = self.name.rsplit(Core.NS_SEP, 1)[0] if self.is_ns else ""

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

    @property
    def nodetype(self) -> str:
        """Determine node type based on summary data."""
        if self.filetype not in (FileType.JOURNAL, FileType.PAGE):
            return Node.OTHER
        match (self.has_backlinks, self.backlinked, self.backlinked_ns_only):
            case (True, True, True) | (True, True, False) | (True, False, True):
                nodetype = Node.BRANCH
            case (True, False, False):
                nodetype = Node.ROOT
            case (False, True, True) | (False, True, False):
                nodetype = Node.LEAF
            case (False, False, True):
                nodetype = Node.ORPHAN_NAMESPACE if self.has_content else Node.ORPHAN_NAMESPACE_TRUE
            case (False, False, False):
                nodetype = Node.ORPHAN_GRAPH if self.has_content else Node.ORPHAN_TRUE
            case _:
                nodetype = Node.OTHER
        return nodetype

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

    def get_data(self, key: str) -> Iterable[str]:
        """Get data by key."""
        return self.data.get(key, ())
