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
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import logseq_analyzer.utils.patterns_content as ContentPatterns

from ..utils.enums import Core, Output, Criteria
from ..utils.helpers import singleton, sort_dict_by_value

if TYPE_CHECKING:
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


@singleton
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

    def init_ns_parts(self, index: "FileIndex") -> None:
        """
        Create namespace parts from the data.
        """
        level_distribution = Counter()
        namespace_data = self.structure.data
        namespace_parts = self.structure.parts
        unique_namespace_parts = self.structure.unique_parts
        unique_namespaces_per_level = self.structure.unique_ns_per_level
        _part_levels = self._part_levels
        _part_entries = self._part_entries
        for file in index:
            if not (curr_ns_info := file.path.ns_info) or not file.path.is_namespace:
                continue
            current_level = self.structure.tree
            namespace_data[file.path.name] = {k: v for k, v in curr_ns_info.__dict__.items() if v}
            if not (parts := namespace_data[file.path.name].get("parts")):
                continue
            namespace_parts[file.path.name] = parts
            for part, level in parts.items():
                unique_namespace_parts.add(part)
                unique_namespaces_per_level[level].add(part)
                level_distribution[level] += 1
                current_level.setdefault(part, {})
                current_level = current_level[part]
                _part_levels[part].add(level)
                _part_entries[part].append({"entry": file.path.name, "level": level})
        self.structure.details["max_depth"] = max(level_distribution) if level_distribution else 0
        self.structure.details["level_distribution"] = dict(level_distribution)

    def analyze_ns_queries(self, index: "FileIndex") -> None:
        """Analyze namespace queries."""
        ns_data = self.structure.data
        ns_queries = {}
        for file in index:
            for query in file.data.get(Criteria.DBC_NAMESPACE_QUERIES.value, []):
                page_refs = ContentPatterns.PAGE_REFERENCE.findall(query)
                if len(page_refs) != 1:
                    logger.warning("Invalid references found in query: %s", query)
                    continue

                page_ref = page_refs[0]
                ns_queries.setdefault(query, {})
                ns_queries[query].setdefault("found_in", []).append(file.path.name)
                ns_queries[query]["namespace"] = page_ref
                ns_queries[query]["size"] = ns_data.get(page_ref, {}).get("size", 0)
                ns_queries[query]["uri"] = file.path.uri
                ns_queries[query]["logseq_url"] = file.path.logseq_url
        self.queries = sort_dict_by_value(ns_queries, value="size", reverse=True)

    def detect_non_ns_conflicts(self, index: "FileIndex", dangling_links: set[str]) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        non_ns_names = []
        for file in index:
            if not file.path.ns_info or file.path.is_namespace:
                continue
            non_ns_names.append(file.path.name)
        unique_namespace_parts = self.structure.unique_parts
        potential_non_ns_names = unique_namespace_parts.intersection(non_ns_names)
        potential_dangling = unique_namespace_parts.intersection(dangling_links)
        conflicts_non_namespace = self.conflicts.non_namespace
        conflicts_dangling = self.conflicts.dangling
        namespace_parts = self.structure.parts

        for entry, parts in namespace_parts.items():
            for part in (part for part in parts if part in potential_non_ns_names):
                conflicts_non_namespace[part].append(entry)
            for part in (part for part in parts if part in potential_dangling):
                conflicts_dangling[part].append(entry)

    def detect_parent_depth_conflicts(self) -> None:
        """Identify namespace parts that appear at different depths (levels) across entries."""
        part_levels = self._part_levels
        part_entries = self._part_entries
        conflicts_parent_depth = self.conflicts.parent_depth
        conflicts_parent_unique = self.conflicts.parent_unique
        for part, levels in part_levels.items():
            if len(levels) < 2:
                continue

            details = part_entries[part]
            for level in levels:
                key = (part, level)
                entries = [d["entry"] for d in details if d["level"] == level]
                conflicts_parent_depth[key] = entries
                for page in entries:
                    parts = page.split(Core.NS_SEP.value)
                    up_to_level = parts[:level]
                    conflicts_parent_unique[key].add(Core.NS_SEP.value.join(up_to_level))

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
