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
from typing import Literal

from ..utils.enums import Core
from ..utils.helpers import singleton, sort_dict_by_value
from ..utils.patterns import ContentPatterns
from .graph import LogseqGraph
from .index import FileIndex, get_attribute_list


@singleton
class LogseqNamespaces:
    """
    Class for analyzing namespace data in Logseq.
    """

    index = FileIndex()

    def __init__(self) -> None:
        """
        Initialize the NamespaceAnalyzer instance.
        """
        self._part_levels = defaultdict(set)
        self._part_entries = defaultdict(list)
        self.namespace_data = {}
        self.namespace_parts = {}
        self.unique_namespace_parts = set()
        self.namespace_details = {}
        self.unique_namespaces_per_level = defaultdict(set)
        self.namespace_queries = {}
        self.tree = {}
        self.conflicts_non_namespace = defaultdict(list)
        self.conflicts_dangling = defaultdict(list)
        self.conflicts_parent_depth = {}
        self.conflicts_parent_unique = {}

    def __repr__(self) -> Literal["LogseqNamespaces()"]:
        """Return a string representation of the NamespaceAnalyzer instance."""
        return "LogseqNamespaces()"

    def __str__(self) -> Literal["LogseqNamespaces"]:
        """Return a string representation of the NamespaceAnalyzer instance."""
        return "LogseqNamespaces"

    def __len__(self) -> int:
        """Return the number of unique namespace parts."""
        return len(self.namespace_data)

    def init_ns_parts(self) -> None:
        """
        Create namespace parts from the data.
        """
        level_distribution = Counter()
        for file in LogseqNamespaces.index.yield_files_with_keys("ns_level"):
            current_level = self.tree
            meta = {k: v for k, v in file.__dict__.items() if "ns_" in k and v}
            self.namespace_data[file.path.name] = meta
            if not (parts := meta.get("ns_parts")):
                continue
            self.namespace_parts[file.path.name] = parts
            for part, level in parts.items():
                self.unique_namespace_parts.add(part)
                self.unique_namespaces_per_level[level].add(part)
                level_distribution[level] += 1
                current_level.setdefault(part, {})
                current_level = current_level[part]
                self._part_levels[part].add(level)
                self._part_entries[part].append({"entry": file.path.name, "level": level})

        self.namespace_details["max_depth"] = max(level_distribution) if level_distribution else 0
        self.namespace_details["level_distribution"] = dict(level_distribution)

    def analyze_ns_queries(self) -> None:
        """
        Analyze namespace queries.
        """
        ns_queries = {}
        for file in LogseqNamespaces.index.files:
            for query in file.data.get("namespace_queries", []):
                page_refs = ContentPatterns().page_reference.findall(query)
                if len(page_refs) != 1:
                    logging.warning("Invalid references found in query: %s", query)
                    continue

                page_ref = page_refs[0]
                ns_queries.setdefault(query, {})
                ns_queries[query].setdefault("found_in", []).append(file.path.name)
                ns_queries[query]["namespace"] = page_ref
                ns_queries[query]["ns_size"] = self.namespace_data.get(page_ref, {}).get("ns_size", 0)
                ns_queries[query]["uri"] = getattr(file, "uri", "")
                ns_queries[query]["logseq_url"] = getattr(file, "logseq_url", "")

        # Sort the queries by size in descending order
        self.namespace_queries = sort_dict_by_value(ns_queries, value="ns_size", reverse=True)

    def detect_non_ns_conflicts(self) -> None:
        """
        Check for conflicts between split namespace parts and existing non-namespace page names.
        """
        non_ns_files = LogseqNamespaces.index.yield_files_without_keys("ns_level")
        non_ns_names = get_attribute_list(non_ns_files, "name")
        potential_non_ns_names = self.unique_namespace_parts.intersection(non_ns_names)
        potential_dangling = self.unique_namespace_parts.intersection(LogseqGraph().dangling_links)
        for entry, parts in self.namespace_parts.items():
            for part in parts:
                if part in potential_non_ns_names:
                    self.conflicts_non_namespace[part].append(entry)
                if part in potential_dangling:
                    self.conflicts_dangling[part].append(entry)

    def detect_parent_depth_conflicts(self) -> None:
        """
        Identify namespace parts that appear at different depths (levels) across entries.
        """
        for part, levels in self._part_levels.items():
            # Filter out parts that only occur at a single depth.
            if len(levels) < 2:
                continue

            details = self._part_entries[part]
            for level in levels:
                key = f"{part} {level}"
                entries = [i["entry"] for i in details if i["level"] == level]
                self.conflicts_parent_depth[key] = entries

                level = int(key.rsplit(" ", maxsplit=1)[-1])
                unique_pages = set()
                for page in entries:
                    parts = page.split(Core.NS_SEP.value)
                    up_to_level = parts[:level]
                    unique_pages.add(Core.NS_SEP.value.join(up_to_level))
                self.conflicts_parent_unique[key] = unique_pages
