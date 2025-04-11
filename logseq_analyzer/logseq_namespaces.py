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
from typing import Generator, List
import logging

from .logseq_graph import LogseqGraph
from .logseq_filename import LogseqFilename
from .utils.patterns import RegexPatterns
from .logseq_analyzer_config import LogseqAnalyzerConfig


class LogseqNamespaces:
    """
    Class for analyzing namespace data in Logseq.
    """

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the NamespaceAnalyzer instance.
        """
        if not hasattr(self, "_initialized"):
            graph = LogseqGraph()
            self._initialized = True
            self._part_levels = defaultdict(set)
            self._part_entries = defaultdict(list)
            self.hashed_files = graph.hashed_files
            self.data = graph.data
            self.dangling_links = graph.dangling_links
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

    def init_ns_parts(self):
        """
        Create namespace parts from the data.
        """
        level_distribution = Counter()
        for file in self.yield_files_with_keys("ns_level"):
            current_level = self.tree
            meta = {k: v for k, v in file.__dict__.items() if "ns_" in k and v}
            self.namespace_data[file.name] = meta
            parts = meta.get("ns_parts")
            if not parts:
                continue
            self.namespace_parts[file.name] = parts
            for part, level in parts.items():
                self.unique_namespace_parts.add(part)
                self.unique_namespaces_per_level[level].add(part)
                level_distribution[level] += 1
                if part not in current_level:
                    current_level[part] = {}
                current_level = current_level[part]
                self._part_levels[part].add(level)
                self._part_entries[part].append({"entry": file.name, "level": level})

        self.namespace_details["max_depth"] = max(level_distribution) if level_distribution else 0
        self.namespace_details["level_distribution"] = dict(level_distribution)

    def analyze_ns_queries(self):
        """
        Analyze namespace queries.
        """
        patterns = RegexPatterns()
        for _, file in self.hashed_files.items():
            got_ns_queries = file.data.get("namespace_queries")
            if not got_ns_queries:
                continue
            for q in got_ns_queries:
                page_refs = patterns.content["page_reference"].findall(q)
                if len(page_refs) != 1:
                    logging.warning("Invalid references found in query: %s", q)
                    continue

                page_ref = page_refs[0]
                self.namespace_queries.setdefault(q, {})
                self.namespace_queries[q].setdefault("found_in", []).append(file.name)
                self.namespace_queries[q]["namespace"] = page_ref
                self.namespace_queries[q]["ns_size"] = self.namespace_data.get(page_ref, {}).get("ns_size", 0)
                self.namespace_queries[q]["uri"] = getattr(file, "uri", "")
                self.namespace_queries[q]["logseq_url"] = getattr(file, "logseq_url", "")

        # Sort the queries by size in descending order
        self.namespace_queries = dict(
            sorted(
                self.namespace_queries.items(),
                key=lambda item: item[1]["ns_size"],
                reverse=True,
            )
        )

    def detect_non_ns_conflicts(self):
        """
        Check for conflicts between split namespace parts and existing non-namespace page names.
        """
        non_ns_names = self.list_files_without_keys("ns_level")
        potential_non_ns_names = self.unique_namespace_parts.intersection(non_ns_names)
        potential_dangling = self.unique_namespace_parts.intersection(self.dangling_links)
        for entry, parts in self.namespace_parts.items():
            for part in parts:
                if part in potential_non_ns_names:
                    self.conflicts_non_namespace[part].append(entry)
                if part in potential_dangling:
                    self.conflicts_dangling[part].append(entry)

    def detect_parent_depth_conflicts(self):
        """
        Identify namespace parts that appear at different depths (levels) across entries.
        """
        ac = LogseqAnalyzerConfig()
        ns_sep = ac.config["CONST"]["NAMESPACE_SEP"]
        for part, levels in self._part_levels.items():
            # Filter out parts that only occur at a single depth.
            if len(levels) < 2:
                continue

            details = self._part_entries[part]
            for level in sorted(levels):
                key = f"{part} {level}"
                entries = [i["entry"] for i in details if i["level"] == level]
                self.conflicts_parent_depth[key] = entries

                level = int(key.rsplit(" ", maxsplit=1)[-1])
                unique_pages = set()
                for page in entries:
                    parts = page.split(ns_sep)
                    up_to_level = parts[:level]
                    unique_pages.add(ns_sep.join(up_to_level))
                self.conflicts_parent_unique[key] = unique_pages

    def yield_files_with_keys(self, *criteria) -> Generator[LogseqFilename, None, None]:
        """
        Extract a subset of the summary data based on whether the keys exists.
        """
        for _, file in self.hashed_files.items():
            if all(hasattr(file, key) for key in criteria):
                yield file

    def list_files_without_keys(self, *criteria) -> List[str]:
        """
        Extract a subset of the summary data based on whether the keys do not exist.
        """
        return [file.name for _, file in self.hashed_files.items() if all(not hasattr(file, key) for key in criteria)]
