"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from collections import Counter

from ..io.cache import Cache
from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria
from ..utils.helpers import singleton, sort_dict_by_value
from .index import FileIndex


@singleton
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    def __init__(self):
        """Initialize the LogseqGraph instance."""
        self.all_linked_references = {}
        self.dangling_links = set()
        self.unique_linked_references = set()
        self.unique_linked_references_ns = set()

    def __repr__(self):
        """Return a string representation of the LogseqGraph instance."""
        return "LogseqGraph()"

    def __str__(self):
        """Return a string representation of the LogseqGraph instance."""
        return "LogseqGraph"

    def __len__(self):
        """Return the number of unique linked references."""
        return len(self.all_linked_references)

    def process_graph_files(self):
        """Process all files in the Logseq graph folder."""
        index = FileIndex()
        cache = Cache()
        for file_path in cache.iter_modified_files():
            file = LogseqFile(file_path)
            file.init_file_data()
            file.process_content_data()
            index.add(file)

    def post_processing_content(self):
        """Post-process the content data for all files."""
        index = FileIndex()
        unique_aliases = set()

        for file in index.files:
            if file.path.is_namespace:
                self.post_processing_content_namespaces(file)

            found_aliases = file.data.get(Criteria.ALIASES.value, [])
            unique_aliases.update(found_aliases)
            linked_references = [
                found_aliases,
                file.data.get(Criteria.DRAWS.value, []),
                file.data.get(Criteria.PAGE_REFERENCES.value, []),
                file.data.get(Criteria.TAGS.value, []),
                file.data.get(Criteria.TAGGED_BACKLINKS.value, []),
                file.data.get(Criteria.PROPERTIES_PAGE_BUILTIN.value, []),
                file.data.get(Criteria.PROPERTIES_PAGE_USER.value, []),
                file.data.get(Criteria.PROPERTIES_BLOCK_BUILTIN.value, []),
                file.data.get(Criteria.PROPERTIES_BLOCK_USER.value, []),
                [getattr(file, "ns_parent", "")],
            ]
            linked_references = [item for sublist in linked_references for item in sublist if item]

            for item in linked_references:
                self.all_linked_references.setdefault(item, {"count": 0, "found_in": Counter()})
                self.all_linked_references[item]["count"] = self.all_linked_references[item].get("count", 0) + 1
                self.all_linked_references[item]["found_in"][file.path.name] += 1

            if ns_parent := getattr(file, "ns_parent", ""):
                linked_references.remove(ns_parent)

            self.unique_linked_references.update(linked_references)

        for _, values in self.all_linked_references.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        self.all_linked_references = sort_dict_by_value(self.all_linked_references, value="count", reverse=True)

        all_file_names = set(index.name_to_files.keys())
        self.dangling_links = self.process_dangling_links(all_file_names, unique_aliases)

    def post_processing_content_namespaces(self, file: LogseqFile):
        """Post-process namespaces in the content data."""
        ns_level = getattr(file, "ns_level")
        ns_root = getattr(file, "ns_root")
        ns_parent = getattr(file, "ns_parent_full")
        self.unique_linked_references_ns.update([ns_root, file.path.name])

        index = FileIndex()
        for ns_root_file in index.get(ns_root):
            if not hasattr(ns_root_file, "ns_level"):
                setattr(ns_root_file, "ns_level", 1)
            if not hasattr(ns_root_file, "ns_children"):
                setattr(ns_root_file, "ns_children", set())
            ns_children_root = getattr(ns_root_file, "ns_children")
            ns_children_root.add(file.path.name)
            setattr(ns_root_file, "ns_size", self.process_ns_size(ns_root_file))

        if ns_level <= 2:
            return

        for ns_parent_file in index.get(ns_parent):
            if not hasattr(ns_parent_file, "ns_level"):
                setattr(ns_parent_file, "ns_level", ns_level - 1)
            if not hasattr(ns_parent_file, "ns_children"):
                setattr(ns_parent_file, "ns_children", set())
            ns_children_parent = getattr(ns_parent_file, "ns_children")
            ns_children_parent.add(file.path.name)
            setattr(ns_parent_file, "ns_size", self.process_ns_size(ns_parent_file))

    def process_ns_size(self, parent_file: LogseqFile) -> int:
        """
        Process the size of namespaces.

        Args:
            parent_file (LogseqFile): The parent file to process.

        Returns:
            int: The size of the namespace.
        """
        if not hasattr(parent_file, "ns_size"):
            ns_children = getattr(parent_file, "ns_children")
            return len(ns_children)
        ns_size = getattr(parent_file, "ns_size")
        return ns_size + 1

    def process_summary_data(self):
        """Process summary data for each file based on metadata and content analysis."""
        index = FileIndex()
        for file in index.files:
            if not file.is_backlinked:
                file.is_backlinked = file.check_is_backlinked(self.unique_linked_references)
            if not file.is_backlinked_by_ns_only:
                file.is_backlinked_by_ns_only = file.check_is_backlinked(self.unique_linked_references_ns)
            if file.is_backlinked and file.is_backlinked_by_ns_only:
                file.is_backlinked = False
            if file.file_type in ("journal", "page"):
                file.node_type = file.determine_node_type()

    def process_dangling_links(self, all_file_names: set[str], unique_aliases: set[str]):
        """Process dangling links in the graph."""
        all_linked_refs = self.unique_linked_references.union(self.unique_linked_references_ns)
        all_linked_refs.difference_update(all_file_names)
        all_linked_refs.difference_update(unique_aliases)
        return set(sorted(all_linked_refs))
