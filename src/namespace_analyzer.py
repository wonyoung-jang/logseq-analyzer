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

from collections import Counter, defaultdict
import logging

from ._global_objects import PATTERNS, ANALYZER_CONFIG
from .process_summary_data import list_files_with_keys, list_files_without_keys


class NamespaceAnalyzer:
    """
    Class for analyzing namespace data in Logseq.

    Attributes:
        namespace_parts (dict): Dictionary mapping entry names to their namespace parts.
        namespace_details (dict): Dictionary containing details about namespaces.
    """

    def __init__(self, data, dangling_links):
        """
        Initialize the NamespaceAnalyzer instance.
        """
        self.data = data
        self.dangling_links = dangling_links
        self.namespace_data = {}
        self.namespace_parts = {}
        self.unique_namespace_parts = set()
        self.namespace_details = {}
        self.unique_namespaces_per_level = {}
        self.namespace_queries = {}
        self.tree = {}
        self.conflicts_non_namespace = {}
        self.conflicts_dangling = {}
        self.conflicts_parent_depth = {}
        self.conflicts_parent_unique = {}

    def init_ns_parts(self):
        """
        Create namespace parts from the data.
        """
        is_namespace = list_files_with_keys(self.data, "namespace_level")
        for name in is_namespace:
            self.namespace_data.setdefault(name, {k: v for k, v in self.data[name].items() if "namespace" in k and v})
        self.namespace_parts = {
            k: v["namespace_parts"] for k, v in self.namespace_data.items() if v.get("namespace_parts")
        }

    def get_unique_ns_parts(self):
        """
        Analyze the levels of namespace parts across all entries.
        """
        for parts in self.namespace_parts.values():
            self.unique_namespace_parts.update(parts.keys())
        return self.unique_namespace_parts

    def analyze_ns_details(self):
        """
        Perform extended analysis on namespace parts.
        """
        level_distribution = Counter()

        for _, parts in self.namespace_parts.items():
            for _, level in parts.items():
                level_distribution[level] += 1

        max_depth = max(level_distribution) if level_distribution else 0

        self.namespace_details = {
            "max_depth": max_depth,
            "level_distribution": dict(level_distribution),
        }

    def get_unique_ns_by_levels(self):
        """
        Get unique namespaces by level.
        """
        self.unique_namespaces_per_level = defaultdict(set)
        for parts in self.namespace_parts.values():
            for part, level in parts.items():
                self.unique_namespaces_per_level[level].add(part)

    def analyze_ns_queries(self):
        """
        Analyze namespace queries.
        """
        self.namespace_queries = {}
        for entry, data in self.data.items():
            got_ns_queries = data.get("namespace_queries")
            if not got_ns_queries:
                continue
            for q in got_ns_queries:
                page_refs = PATTERNS.content["page_reference"].findall(q)
                if len(page_refs) != 1:
                    logging.warning("Invalid references found in query: %s", q)
                    continue

                page_ref = page_refs[0]
                self.namespace_queries[q] = self.namespace_queries.get(q, {})
                self.namespace_queries[q]["found_in"] = self.namespace_queries[q].get("found_in", [])
                self.namespace_queries[q]["found_in"].append(entry)
                self.namespace_queries[q]["namespace"] = page_ref
                self.namespace_queries[q]["size"] = self.namespace_data.get(page_ref, {}).get("namespace_size", 0)
                self.namespace_queries[q]["uri"] = self.data[entry].get("uri", "")
                self.namespace_queries[q]["logseq_url"] = self.data[entry].get("logseq_url", "")

        # Sort the queries by size in descending order
        self.namespace_queries = dict(
            sorted(self.namespace_queries.items(), key=lambda item: item[1]["size"], reverse=True)
        )

    def build_ns_tree(self):
        """
        Build a tree-like structure of namespaces.
        """
        for _, parts in self.namespace_parts.items():
            current_level = self.tree
            for part_level in parts.items():
                part = part_level[0]
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]

    def detect_non_ns_conflicts(self):
        """
        Check for conflicts between split namespace parts and existing non-namespace page names.
        """
        non_ns_names = list_files_without_keys(self.data, "namespace_level")
        potential_non_ns_names = self.unique_namespace_parts.intersection(non_ns_names)
        potential_dangling = self.unique_namespace_parts.intersection(self.dangling_links)
        self.conflicts_non_namespace = defaultdict(list)
        self.conflicts_dangling = defaultdict(list)
        for entry, parts in self.namespace_parts.items():
            for part in parts:
                if part in potential_non_ns_names:
                    self.conflicts_non_namespace[part].append(entry)
                if part in potential_dangling:
                    self.conflicts_dangling[part].append(entry)

    def detect_parent_depth_conflicts(self):
        """
        Identify namespace parts that appear at different depths (levels) across entries.

        For each namespace part, we collect the levels at which it appears as well as
        the associated entries. Parts that occur at more than one depth are flagged
        as potential conflicts.
        """
        # Mapping from namespace part to a set of levels and associated entries
        part_levels = defaultdict(set)
        part_entries = defaultdict(list)

        for entry, parts in self.namespace_parts.items():
            for part, level in parts.items():
                part_levels[part].add(level)
                part_entries[part].append({"entry": entry, "level": level})

        # Filter out parts that only occur at a single depth.
        conflicts = {}
        for part, levels in part_levels.items():
            if len(levels) > 1:
                conflicts[part] = {"levels": sorted(list(levels)), "entries": part_entries[part]}

        # Split so it's dict[part level] = [list of parts]
        for part, details in conflicts.items():
            for level in details["levels"]:
                self.conflicts_parent_depth[f"{part} {level}"] = [
                    i["entry"] for i in details["entries"] if i["level"] == level
                ]

    def get_unique_parent_conflicts(self):
        """
        Get unique conflicts for each namespace part.
        """
        ns_sep = ANALYZER_CONFIG.get("LOGSEQ_NAMESPACES", "NAMESPACE_SEP")
        for part, details in self.conflicts_parent_depth.items():
            level = int(part.split(" ")[-1])
            unique_pages = set()
            for page in details:
                parts = page.split(ns_sep)
                up_to_level = parts[:level]
                unique_pages.add(ns_sep.join(up_to_level))
            self.conflicts_parent_unique[part] = unique_pages
