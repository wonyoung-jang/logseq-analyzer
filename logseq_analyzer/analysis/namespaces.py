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
from typing import TYPE_CHECKING, Any

from logseq_analyzer.utils.enums import Core, Crit, Output, OutputDir
from logseq_analyzer.utils.helpers import sort_dict_by_value
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from logseq_analyzer.analysis.file import LogseqFile
    from logseq_analyzer.analysis.index import FileIndex

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    index: FileIndex
    dangling_links: set[str]
    _level_dist: Counter = field(default_factory=Counter)
    _part_levels: defaultdict[str, set[int]] = field(default_factory=lambda: defaultdict(set))
    _part_entries: defaultdict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    cnflcts_dangling: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    cnflcts_non_namespace: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    cnflcts_parent_depth: dict[tuple[str, int], list[str]] = field(default_factory=lambda: defaultdict(list))
    cnflcts_parent_unique: dict[tuple[str, int], set[str]] = field(default_factory=lambda: defaultdict(set))
    data: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    parts: dict[str, Any] = field(default_factory=dict)
    tree: dict[str, Any] = field(default_factory=dict)
    unique_ns_per_level: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_parts: set[str] = field(default_factory=set)
    queries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqNamespaces instance."""
        self.init_ns_parts()
        self.analyze_ns_queries()
        self.detect_non_ns_conflicts()
        self.detect_parent_depth_conflicts()

    def init_ns_parts(self) -> None:
        """Create namespace parts from the data."""
        for f in self.index:
            self._init_ns_parts(f)
        self.details["level_distribution"] = dict(self._level_dist)

    def analyze_ns_queries(self) -> None:
        """Analyze namespace queries."""
        for f in self.index:
            self._analyze_ns_queries(f)
        self.queries = sort_dict_by_value(self.queries, value="size", reverse=True)

    def _init_ns_parts(self, f: LogseqFile) -> None:
        """Initialize namespace parts for a given file."""
        if not f.info.namespace.is_namespace:
            return
        self.data[f.path.name] = {k: getattr(f.info.namespace, k) for k in f.info.namespace.__slots__}
        if not (parts := self.data[f.path.name].get("parts")):
            return
        self.parts[f.path.name] = parts
        _curr_tree_lvl = self.tree
        for part, level in parts.items():
            self.unique_parts.add(part)
            self.unique_ns_per_level[level].add(part)
            self._level_dist[level] += 1
            _curr_tree_lvl.setdefault(part, {})
            _curr_tree_lvl = _curr_tree_lvl[part]
            self._part_levels[part].add(level)
            self._part_entries[part].append({"entry": f.path.name, "level": level})

    def _analyze_ns_queries(self, f: LogseqFile) -> None:
        if not (f_data := f.data):
            return
        if not (queries := f_data.get(Crit.DblCurly.NAMESPACE_QUERY)):
            return
        for query in queries:
            if not ContentPatterns.PAGE_REFERENCE.search(query):
                logger.warning("Invalid query found: %s", query)
                continue
            page_refs = ContentPatterns.PAGE_REFERENCE.findall(query)
            if len(page_refs) != 1:
                logger.warning("Invalid references found in query: %s", query)
                continue
            self.queries.setdefault(query, {})
            self.queries[query].setdefault("found_in", []).append(f.path.name)
            self.queries[query]["namespace"] = page_refs[0]
            self.queries[query]["size"] = self.data.get(page_refs[0], {}).get("size", 0)
            self.queries[query]["uri"] = f.path.uri
            self.queries[query]["logseq_url"] = f.path.logseq_url

    def detect_non_ns_conflicts(self) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        potential_non_ns_names = self.unique_parts.intersection(self.index.yield_non_ns_names())
        potential_dangling = self.unique_parts.intersection(self.dangling_links)
        for entry, parts in self.parts.items():
            for part in potential_non_ns_names.intersection(parts):
                self.cnflcts_non_namespace[part].append(entry)
            for part in potential_dangling.intersection(parts):
                self.cnflcts_dangling[part].append(entry)

    def detect_parent_depth_conflicts(self) -> None:
        """Identify namespace parts that appear at different depths (levels) across entries."""
        for part, levels in self._part_levels.items():
            if len(levels) < 2:
                continue
            for level in levels:
                key = (part, level)
                entries = (d["entry"] for d in self._part_entries[part] if d["level"] == level)
                for entry in entries:
                    up_to_level = entry.split(Core.NS_SEP)[:level]
                    self.cnflcts_parent_unique[key].add(Core.NS_SEP.join(up_to_level))
                    self.cnflcts_parent_depth[key].append(entry)

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the namespace analysis."""
        return {
            OutputDir.NAMESPACES: {
                Output.NS_CONFLICTS_DANGLING: self.cnflcts_dangling,
                Output.NS_CONFLICTS_NON_NAMESPACE: self.cnflcts_non_namespace,
                Output.NS_CONFLICTS_PARENT_DEPTH: self.cnflcts_parent_depth,
                Output.NS_CONFLICTS_PARENT_UNIQUE: self.cnflcts_parent_unique,
                Output.NS_DATA: self.data,
                Output.NS_DETAILS: self.details,
                Output.NS_HIERARCHY: self.tree,
                Output.NS_PARTS: self.parts,
                Output.NS_UNIQUE_PARTS: self.unique_parts,
                Output.NS_UNIQUE_PER_LEVEL: self.unique_ns_per_level,
                Output.NS_QUERIES: self.queries,
            }
        }
