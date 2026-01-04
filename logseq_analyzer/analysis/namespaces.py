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

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import logseq_analyzer.patterns.content as content_patterns

from ..utils.enums import Core, CritDblCurly, Output
from ..utils.helpers import sort_dict_by_value

if TYPE_CHECKING:
    from .index import FileIndex

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class NamespaceConflicts:
    """Class to hold namespace conflict data."""

    dangling: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    non_namespace: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    parent_depth: dict[tuple[str, int], list[str]] = field(default_factory=lambda: defaultdict(list))
    parent_unique: dict[tuple[str, int], set[str]] = field(default_factory=lambda: defaultdict(set))


@dataclass(slots=True)
class NamespaceStructure:
    """Class to hold namespace structure data."""

    data: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    parts: dict[str, Any] = field(default_factory=dict)
    tree: dict[str, Any] = field(default_factory=dict)
    unique_ns_per_level: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_parts: set[str] = field(default_factory=set)


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    index: FileIndex
    dangling_links: list[str]
    _part_levels: defaultdict[str, set[int]] = field(default_factory=lambda: defaultdict(set))
    _part_entries: defaultdict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    conflicts: NamespaceConflicts = field(default_factory=NamespaceConflicts)
    structure: NamespaceStructure = field(default_factory=NamespaceStructure)
    queries: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqNamespaces instance."""
        self.process()

    def process(self) -> None:
        """Process the namespace data from the index."""
        self.init_ns_parts()
        self.analyze_ns_queries()
        self.detect_non_ns_conflicts()
        self.detect_parent_depth_conflicts()

    def init_ns_parts(self) -> None:
        """Create namespace parts from the data."""
        _structure = self.structure
        details = _structure.details
        unique_parts_add = _structure.unique_parts.add
        unique_ns_per_level = _structure.unique_ns_per_level
        data = _structure.data
        part_levels = self._part_levels
        part_entries = self._part_entries
        level_distribution = Counter()
        for f in self.index:
            if not f.info.namespace.is_namespace:
                continue
            current_level = _structure.tree
            f_name = f.path.name
            data[f_name] = {
                k: getattr(f.info.namespace, k) for k in f.info.namespace.__slots__ if hasattr(f.info.namespace, k)
            }
            if not (parts := data[f_name].get("parts")):
                continue
            _structure.parts[f_name] = parts
            for part, level in parts.items():
                unique_parts_add(part)
                unique_ns_per_level[level].add(part)
                level_distribution[level] += 1
                current_level.setdefault(part, {})
                current_level = current_level[part]
                part_levels[part].add(level)
                part_entries[part].append({"entry": f_name, "level": level})
        details["level_distribution"] = dict(level_distribution)

    def analyze_ns_queries(self) -> None:
        """Analyze namespace queries."""
        get_structure = self.structure.data.get
        search_page_ref_pattern = content_patterns.PAGE_REFERENCE.search
        find_all_page_ref_pattern = content_patterns.PAGE_REFERENCE.findall
        ns_queries = self.queries
        for f in self.index:
            if not (f_data := f.data):
                continue

            if not (queries := f_data.get(CritDblCurly.NAMESPACE_QUERIES)):
                continue

            f_path = f.path
            for query in queries:
                if not search_page_ref_pattern(query):
                    logger.warning("Invalid query found: %s", query)
                    continue

                page_refs = find_all_page_ref_pattern(query)

                if len(page_refs) != 1:
                    logger.warning("Invalid references found in query: %s", query)
                    continue

                page_ref = page_refs[0]
                ns_queries.setdefault(query, {})
                ns_queries[query].setdefault("found_in", []).append(f_path.name)
                ns_queries[query]["namespace"] = page_ref
                ns_queries[query]["size"] = get_structure(page_ref, {}).get("size", 0)
                ns_queries[query]["uri"] = f_path.uri
                ns_queries[query]["logseq_url"] = f_path.logseq_url
        self.queries = sort_dict_by_value(ns_queries, value="size", reverse=True)

    def detect_non_ns_conflicts(self) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        index = self.index
        parts_items = self.structure.parts.items()
        unique_parts = self.structure.unique_parts
        non_ns_conflicts = self.conflicts.non_namespace
        dangling_conflicts = self.conflicts.dangling
        non_ns_names = (f.path.name for f in index if not f.info.namespace.is_namespace)
        potential_non_ns_names = unique_parts.intersection(non_ns_names)
        potential_dangling = unique_parts.intersection(self.dangling_links)
        intersect_non_ns = potential_non_ns_names.intersection
        intersect_dangling = potential_dangling.intersection

        for entry, parts in parts_items:
            for part in intersect_non_ns(parts):
                non_ns_conflicts[part].append(entry)
            for part in intersect_dangling(parts):
                dangling_conflicts[part].append(entry)

    def detect_parent_depth_conflicts(self) -> None:
        """Identify namespace parts that appear at different depths (levels) across entries."""
        part_levels = self._part_levels.items()
        part_entries = self._part_entries
        parent_depth_conflicts = self.conflicts.parent_depth
        parent_unique_conflicts = self.conflicts.parent_unique
        join_to_ns_sep = Core.NS_SEP.join
        for part, levels in part_levels:
            if len(levels) < 2:
                continue

            details = part_entries[part]

            for level in levels:
                key = (part, level)
                entries = (d["entry"] for d in details if d["level"] == level)

                for entry in entries:
                    up_to_level = entry.split(Core.NS_SEP)[:level]
                    parent_unique_conflicts[key].add(join_to_ns_sep(up_to_level))
                    parent_depth_conflicts[key].append(entry)

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the namespace analysis."""
        return {
            Output.NS_CONFLICTS_DANGLING: self.conflicts.dangling,
            Output.NS_CONFLICTS_NON_NAMESPACE: self.conflicts.non_namespace,
            Output.NS_CONFLICTS_PARENT_DEPTH: self.conflicts.parent_depth,
            Output.NS_CONFLICTS_PARENT_UNIQUE: self.conflicts.parent_unique,
            Output.NS_DATA: self.structure.data,
            Output.NS_DETAILS: self.structure.details,
            Output.NS_HIERARCHY: self.structure.tree,
            Output.NS_PARTS: self.structure.parts,
            Output.NS_QUERIES: self.queries,
            Output.NS_UNIQUE_PARTS: self.structure.unique_parts,
            Output.NS_UNIQUE_PER_LEVEL: self.structure.unique_ns_per_level,
        }
