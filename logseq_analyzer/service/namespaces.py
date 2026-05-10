"""Module containing functions for processing and analyzing namespace data in Logseq.

What are the problems trying to be solved?
Logseq's move to a database system from a markdown one.
Currently, namespace pages are full and valid, so root/parent/child is a name.
The proposed migration by Logseq is to split each part and tag the children with their parents.
Now we have three pages of root, parent, and child.
Problems:
    1. The split namespace parts may conflict with existing, non-namespace pages.
    2. Some parents may appear across multiple namespaces at different depths.
    3. There is no easy way to get data about namespaces.
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict

from logseq_analyzer.utils.enums import Core, Crit, Output, OutputDir
from logseq_analyzer.utils.helpers import sort_dict_by_value
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from logseq_analyzer.domain.file import LogseqFile
    from logseq_analyzer.domain.index import FileIndex

logger = logging.getLogger(__name__)

type _NsSlotData = dict[str, object]
type _NsTree = dict[str, "_NsTree"]


class _PartEntry(TypedDict):
    entry: str
    level: int


class _QueryInfo(TypedDict, total=False):
    found_in: list[str]
    namespace: str
    size: int
    uri: str
    logseq_url: str


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    index: FileIndex
    dangling_links: set[str]
    _part_levels: defaultdict[str, set[int]] = field(default_factory=lambda: defaultdict(set))
    _part_entries: defaultdict[str, list[_PartEntry]] = field(default_factory=lambda: defaultdict(list))
    conflicts_dangling: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    conflicts_non_namespace: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    conflicts_parent_depth: dict[tuple[str, int], list[str]] = field(default_factory=lambda: defaultdict(list))
    conflicts_parent_unique: dict[tuple[str, int], set[str]] = field(default_factory=lambda: defaultdict(set))
    data: dict[str, _NsSlotData] = field(default_factory=dict)
    details: dict[str, Counter[int]] = field(default_factory=dict)
    parts: dict[str, dict[str, int]] = field(default_factory=dict)
    tree: _NsTree = field(default_factory=dict)
    unique_ns_per_level: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_parts: set[str] = field(default_factory=set)
    queries: dict[str, _QueryInfo] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqNamespaces instance."""
        self.init_ns_parts()
        self.analyze_ns_queries()
        self.analyze_ns_conflicts()

    def init_ns_parts(self) -> None:
        """Create namespace parts from the data."""
        self.details["level_distribution"] = Counter()
        for f in self.index:
            self._init_ns_parts(f)

    def analyze_ns_queries(self) -> None:
        """Analyze namespace queries."""
        for f in self.index:
            self._analyze_ns_queries(f)
        self.queries = sort_dict_by_value(self.queries, value="size", reverse=True)

    def _init_ns_parts(self, f: LogseqFile) -> None:
        """Initialize namespace parts for a given file."""
        if not f.info.namespace.is_namespace:
            return
        self.data[f.path.name] = f.info.namespace.as_dict
        if not (parts := f.info.namespace.parts):
            return
        self.parts[f.path.name] = parts
        cur = self.tree
        for part, level in parts.items():
            self.unique_parts.add(part)
            self.unique_ns_per_level[level].add(part)
            self.details["level_distribution"][level] += 1
            cur = cur.setdefault(part, {})
            self._part_levels[part].add(level)
            self._part_entries[part].append({"entry": f.path.name, "level": level})

    def _analyze_ns_queries(self, f: LogseqFile) -> None:
        if not (f_data := f.data):
            return
        if not (queries := f_data.get(Crit.DblCurly.NAMESPACE_QUERY)):
            return
        for query in queries:
            page_refs: list[str] = ContentPatterns.PAGE_REFERENCE.findall(query)
            if len(page_refs) != 1:
                logger.warning("Invalid query: %s", query)
                continue
            qinfo = self.queries.setdefault(query, {})
            qinfo.setdefault("found_in", []).append(f.path.name)
            qinfo["namespace"] = page_refs[0]
            qinfo["size"] = (
                _s if (_d := self.data.get(page_refs[0])) and (_s := _d.get("size")) and isinstance(_s, int) else 0
            )
            qinfo["uri"] = f.path.uri
            qinfo["logseq_url"] = f.path.logseq_url

    def analyze_ns_conflicts(self) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        potential_non_ns = self.unique_parts.intersection(self.index.yield_non_ns_names())
        potential_dangling = self.unique_parts.intersection(self.dangling_links)
        for entry, parts in self.parts.items():
            for part in potential_non_ns.intersection(parts):
                self.conflicts_non_namespace[part].append(entry)
            for part in potential_dangling.intersection(parts):
                self.conflicts_dangling[part].append(entry)
        for part, levels in self._part_levels.items():
            if len(levels) < 2:
                continue
            for level in levels:
                key = (part, level)
                entries = (d["entry"] for d in self._part_entries[part] if d["level"] == level)
                for entry in entries:
                    up_to_level = entry.split(Core.NS_SEP)[:level]
                    self.conflicts_parent_unique[key].add(Core.NS_SEP.join(up_to_level))
                    self.conflicts_parent_depth[key].append(entry)

    @property
    def report(self) -> dict[str, object]:
        """Generate a report of the namespace analysis."""
        return {
            OutputDir.NAMESPACES: {
                Output.NS_CONFLICTS_DANGLING: self.conflicts_dangling,
                Output.NS_CONFLICTS_NON_NAMESPACE: self.conflicts_non_namespace,
                Output.NS_CONFLICTS_PARENT_DEPTH: self.conflicts_parent_depth,
                Output.NS_CONFLICTS_PARENT_UNIQUE: self.conflicts_parent_unique,
                Output.NS_DATA: self.data,
                Output.NS_DETAILS: self.details,
                Output.NS_HIERARCHY: self.tree,
                Output.NS_PARTS: self.parts,
                Output.NS_UNIQUE_PARTS: self.unique_parts,
                Output.NS_UNIQUE_PER_LEVEL: self.unique_ns_per_level,
                Output.NS_QUERIES: self.queries,
            }
        }
