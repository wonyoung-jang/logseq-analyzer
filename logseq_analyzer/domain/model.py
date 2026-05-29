"""Domain model classes for Logseq graph and files."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from logseq_analyzer.domain.enums import Crit, FileType
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

LOGSEQ_BUILTIN_PROPERTY: frozenset[str] = frozenset(
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


class NodeType(StrEnum):
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
    bracket_level = 0
    curr = []
    iterator = iter(enumerate(aliases))
    for i, char in iterator:
        if char == "[" and aliases[i : i + 2] == "[[":
            bracket_level += 1
            next(iterator, None)  # skip second '['
        elif char == "]" and aliases[i : i + 2] == "]]":
            if bracket_level > 0:
                bracket_level -= 1
            next(iterator, None)  # skip second ']'
        elif char == "," and bracket_level == 0:
            if val := "".join(curr).strip().lower():
                yield val
            curr.clear()
        else:
            curr.append(char)
    if val := "".join(curr).strip().lower():
        yield val


def _parse_hls_bullet(bullet: str) -> str | None:
    """Parse the first bullet of an HLS file to extract the page name."""
    if not bullet.startswith("[:span]"):
        return None
    props = {m.group(1): m.group(2).strip() for m in ContentPatterns.PROPERTY_VALUE.finditer(bullet)}
    hl_page = props.get("hl-page", "")
    id_ = props.get("id", "")
    hl_stamp = props.get("hl-stamp", "")
    if hl_page and id_ and hl_stamp:
        return f"{hl_page}_{id_}_{hl_stamp}"
    return None


def extract_data_from_content(content: str) -> Iterator[tuple[str, Iterable[str]]]:
    """Extract all relevant data from the content."""
    yield from _extract_masked(content)
    yield from _extract_raw(content)
    yield from _extract_properties(content)
    yield from _extract_hierarchical(content)


def _extract_masked(content: str) -> Iterator[tuple[str, Iterable[str]]]:
    """Extract masked content for all patterns."""
    masked = content
    for p, r in MASK_PATTERN:
        masked = r.sub(f"__{p}__", masked)
    yield from ((p, r.findall(masked)) for p, r in CORE_PATTERN)


def _extract_raw(content: str) -> Iterator[tuple[str, Iterable[str]]]:
    """Extract raw content for all patterns."""
    yield from ((p, r.findall(content)) for p, r in RAW_PATTERN)


def _extract_properties(content: str) -> Iterator[tuple[str, Iterable[str]]]:
    """Extract properties from content."""
    propvalues = dict(ContentPatterns.PROPERTY_VALUE.findall(content))
    yield Crit.Prop.VALUES, propvalues
    yield Crit.Content.ALIAS, tuple(_process_aliases(propvalues.get("alias", "")))
    bullet = [b.strip("\t \n") for b in ContentPatterns.BULLET.split(content)]
    firstbullet = bullet[0] if bullet else ""
    if firstbullet and not firstbullet.startswith("#"):
        prop_page = set(ContentPatterns.PROPERTY.findall(firstbullet))
        prop_block = set(ContentPatterns.PROPERTY.findall("\n".join(bullet[1:])))
    else:
        prop_page = set()
        prop_block = set(propvalues.keys())
    yield Crit.Prop.BLOCK_BUILTIN, tuple(prop_block.intersection(LOGSEQ_BUILTIN_PROPERTY))
    yield Crit.Prop.BLOCK_USER, tuple(prop_block.difference(LOGSEQ_BUILTIN_PROPERTY))
    yield Crit.Prop.PAGE_BUILTIN, tuple(prop_page.intersection(LOGSEQ_BUILTIN_PROPERTY))
    yield Crit.Prop.PAGE_USER, tuple(prop_page.difference(LOGSEQ_BUILTIN_PROPERTY))
    hls_bullets = (_parse_hls_bullet(b) for b in bullet)
    yield Crit.Content.HLS_BULLET, tuple(b for b in hls_bullets if b is not None)


def _extract_hierarchical(content: str) -> Iterator[tuple[str, str]]:
    """Extract hierarchical patterns from content."""
    data = defaultdict(list)
    for ptn in HIERARCHICAL_PATTERN:
        for p, v in ptn.process_hierarchy(content):
            data[p].append(v)
    yield from data.items()


@dataclass(slots=True)
class LogseqNode:
    """A class to represent a Logseq file with additional analysis attributes."""

    path: Path
    name: str
    filetype: str
    ns_root: str
    ns_parent: str
    has_content: bool
    has_backlinks: bool
    data: dict[str, Iterable[str]] = field(repr=False)
    nodetype: str = NodeType.OTHER
    backlinked: bool = False
    backlinked_ns_only: bool = False
    is_ns: bool = False

    def __post_init__(self) -> None:
        """Post-initialization."""
        if not self.is_ns:
            self.is_ns = bool(self.ns_root)

    def __hash__(self) -> int:
        """Return the hash of the LogseqNode based on its file path."""
        return hash(self.path)

    def __eq__(self, other: object) -> bool:
        """Check equality based on file path."""
        return isinstance(other, LogseqNode) and self.path == other.path

    def get_nodetype(self) -> str:
        """Determine node type based on summary data."""
        nodetype = NodeType.OTHER
        if self.filetype in (FileType.JOURNAL, FileType.PAGE):
            match (self.has_backlinks, self.backlinked, self.backlinked_ns_only):
                case (True, True, True) | (True, True, False) | (True, False, True):
                    nodetype = NodeType.BRANCH
                case (True, False, False):
                    nodetype = NodeType.ROOT
                case (False, True, True) | (False, True, False):
                    nodetype = NodeType.LEAF
                case (False, False, True):
                    nodetype = NodeType.ORPHAN_NAMESPACE if self.has_content else NodeType.ORPHAN_NAMESPACE_TRUE
                case (False, False, False):
                    nodetype = NodeType.ORPHAN_GRAPH if self.has_content else NodeType.ORPHAN_TRUE
        return nodetype

    def get_data(self, key: str) -> Iterable[str]:
        """Get data by key."""
        return self.data.get(key, ())
