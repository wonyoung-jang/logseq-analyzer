"""
This module contains functions for processing and analyzing namespace data in Logseq.

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
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

import logseq_analyzer.patterns.content as ContentPatterns

from ..utils.enums import Core, Criteria, Output
from ..utils.helpers import sort_dict_by_value
from .index import FileIndex

logger = logging.getLogger(__name__)


@dataclass
class NamespaceConflicts:
    """Class to hold namespace conflict data."""

    dangling: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    non_namespace: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    parent_depth: dict[str, list[str]] = field(default_factory=dict)
    parent_unique: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))


@dataclass
class NamespaceStructure:
    """
    Class to hold namespace structure data.
    """

    data: dict[str, Any] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    parts: dict[str, Any] = field(default_factory=dict)
    tree: dict[str, Any] = field(default_factory=dict)
    unique_ns_per_level: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_parts: set[str] = field(default_factory=set)


class LogseqNamespaces:
    """
    Class for analyzing namespace data in Logseq.
    """

    __slots__ = (
        "_part_entries",
        "_part_levels",
        "conflicts",
        "queries",
        "structure",
    )

    def __init__(self) -> None:
        """
        Initialize the LogseqNamespaces instance.
        """
        self._part_levels: defaultdict[str, set[int]] = defaultdict(set)
        self._part_entries: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        self.conflicts: NamespaceConflicts = NamespaceConflicts()
        self.queries: dict[str, dict[str, Any]] = {}
        self.structure: NamespaceStructure = NamespaceStructure()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqNamespaces instance."""
        return f"{self.__class__.__name__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqNamespaces instance."""
        return f"{self.__class__.__name__}"

    def process(self, index: FileIndex, dangling_links: set[str]) -> None:
        """
        Process the namespace data from the index.
        """
        self.init_ns_parts(index)
        self.analyze_ns_queries(index)
        self.detect_non_ns_conflicts(index, dangling_links)
        self.detect_parent_depth_conflicts()

    def init_ns_parts(self, index: FileIndex) -> None:
        """
        Create namespace parts from the data.
        """
        structure = self.structure
        part_levels = self._part_levels
        part_entries = self._part_entries
        level_distribution = Counter()
        for f in index:
            if not f.is_namespace:
                continue
            current_level = structure.tree
            structure.data[f.name] = {k: v for k, v in f.ns_info.__dict__.items() if v}
            if not (parts := structure.data[f.name].get("parts")):
                continue
            structure.parts[f.name] = parts
            for part, level in parts.items():
                structure.unique_parts.add(part)
                structure.unique_ns_per_level[level].add(part)
                level_distribution[level] += 1
                current_level.setdefault(part, {})
                current_level = current_level[part]
                part_levels[part].add(level)
                part_entries[part].append({"entry": f.name, "level": level})
        structure.details["level_distribution"] = dict(level_distribution)

    def analyze_ns_queries(self, index: FileIndex) -> None:
        """Analyze namespace queries."""
        structure = self.structure
        ns_query_crit: str = Criteria.DBC_NAMESPACE_QUERIES.value
        page_ref_pattern: re.Pattern = ContentPatterns.PAGE_REFERENCE
        ns_queries = {}
        for f in index:
            for query in f.data.get(ns_query_crit, []):
                page_refs = page_ref_pattern.findall(query)
                if len(page_refs) != 1:
                    logger.warning("Invalid references found in query: %s", query)
                    continue
                ns_queries.setdefault(query, {})
                ns_queries[query].setdefault("found_in", []).append(f.name)
                ns_queries[query]["namespace"] = page_refs[0]
                ns_queries[query]["size"] = structure.data.get(page_refs[0], {}).get("size", 0)
                ns_queries[query]["uri"] = f.uri
                ns_queries[query]["logseq_url"] = f.logseq_url
        self.queries.update(sort_dict_by_value(ns_queries, value="size", reverse=True))

    def detect_non_ns_conflicts(self, index: FileIndex, dangling_links: set[str]) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        structure = self.structure
        conflicts = self.conflicts
        non_ns_names = (f.name for f in index if not f.is_namespace)
        potential_non_ns_names = structure.unique_parts.intersection(non_ns_names)
        potential_dangling = structure.unique_parts.intersection(dangling_links)
        for entry, parts in structure.parts.items():
            for part in potential_non_ns_names.intersection(parts):
                conflicts.non_namespace[part].append(entry)
            for part in potential_dangling.intersection(parts):
                conflicts.dangling[part].append(entry)

    def detect_parent_depth_conflicts(self) -> None:
        """Identify namespace parts that appear at different depths (levels) across entries."""
        ns_sep: str = Core.NS_SEP.value
        part_levels = self._part_levels
        part_entries = self._part_entries
        conflicts = self.conflicts
        for part, levels in part_levels.items():
            if len(levels) < 2:
                continue
            details = part_entries[part]
            for level in levels:
                key = (part, level)
                entries = [d["entry"] for d in details if d["level"] == level]
                conflicts.parent_depth[key] = entries
                for page in entries:
                    parts = page.split(ns_sep)
                    up_to_level = parts[:level]
                    conflicts.parent_unique[key].add(ns_sep.join(up_to_level))

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the namespace analysis."""
        return {
            Output.NS_CONFLICTS_DANGLING.value: self.conflicts.dangling,
            Output.NS_CONFLICTS_NON_NAMESPACE.value: self.conflicts.non_namespace,
            Output.NS_CONFLICTS_PARENT_DEPTH.value: self.conflicts.parent_depth,
            Output.NS_CONFLICTS_PARENT_UNIQUE.value: self.conflicts.parent_unique,
            Output.NS_DATA.value: self.structure.data,
            Output.NS_DETAILS.value: self.structure.details,
            Output.NS_HIERARCHY.value: self.structure.tree,
            Output.NS_PARTS.value: self.structure.parts,
            Output.NS_QUERIES.value: self.queries,
            Output.NS_UNIQUE_PARTS.value: self.structure.unique_parts,
            Output.NS_UNIQUE_PER_LEVEL.value: self.structure.unique_ns_per_level,
        }
