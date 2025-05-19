"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from collections import Counter
from typing import Literal

from ..config.builtin_properties import get_not_builtin_properties
from ..io.cache import Cache
from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria
from ..utils.helpers import singleton, sort_dict_by_value
from .index import FileIndex


@singleton
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    __slots__ = (
        "all_linked_references",
        "all_dangling_links",
        "dangling_links",
        "unique_linked_references",
        "unique_linked_references_ns",
    )

    def __init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.all_linked_references = {}
        self.all_dangling_links = {}
        self.dangling_links = []
        self.unique_linked_references = set()
        self.unique_linked_references_ns = set()

    def __repr__(self) -> Literal["LogseqGraph()"]:
        """Return a string representation of the LogseqGraph instance."""
        return "LogseqGraph()"

    def __str__(self) -> Literal["LogseqGraph"]:
        """Return a string representation of the LogseqGraph instance."""
        return "LogseqGraph"

    def __len__(self) -> int:
        """Return the number of unique linked references."""
        return len(self.all_linked_references)

    @staticmethod
    def process_graph_files(index: FileIndex) -> None:
        """Process all files in the Logseq graph folder."""
        cache = Cache()
        for file_path in cache.iter_modified_files():
            file = LogseqFile(file_path)
            file.init_file_data()
            if file.stat.has_content:
                file.process_content_data()
            index.add(file)

    def post_processing_content(self, index: FileIndex) -> None:
        """Post-process the content data for all files."""
        all_linked_references = {}
        unique_aliases = set()
        unique_linked_references = set()
        unique_linked_references_ns = set()
        for file in index:
            if file.path.is_namespace:
                ns_refs = self._post_processing_content_namespaces(file, index)
                unique_linked_references_ns.update(ns_refs)
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
                [file.path.ns_parent],
            ]
            linked_references = [item for sublist in linked_references for item in sublist if item]
            for item in linked_references:
                all_linked_references.setdefault(item, {"count": 0, "found_in": Counter()})
                all_linked_references[item]["count"] = all_linked_references[item].get("count", 0) + 1
                all_linked_references[item]["found_in"][file.path.name] += 1
            if ns_parent := file.path.ns_parent:
                linked_references.remove(ns_parent)
            unique_linked_references.update(linked_references)
        self.unique_linked_references = unique_linked_references
        self.unique_linked_references_ns = unique_linked_references_ns
        for _, values in all_linked_references.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        all_linked_references = sort_dict_by_value(all_linked_references, value="count", reverse=True)
        all_file_names = (file.path.name for file in index)
        dangling_links = self._process_dangling_links(all_file_names, unique_aliases)
        all_dangling_links = {k: v for k, v in all_linked_references.items() if k in dangling_links}
        self.dangling_links = dangling_links
        self.all_linked_references = all_linked_references
        self.all_dangling_links = all_dangling_links

    @staticmethod
    def _post_processing_content_namespaces(file: LogseqFile, index: FileIndex) -> tuple[str, str]:
        """Post-process namespaces in the content data."""
        ns_level = file.path.ns_level
        ns_root = file.path.ns_root
        ns_parent = file.path.ns_parent_full
        ns_refs = (ns_root, file.path.name)

        for ns_root_file in index[ns_root]:
            ns_root_file: LogseqFile
            ns_root_file.path.is_namespace = True
            ns_root_file.path.ns_level = 1
            ns_root_file.path.ns_children.add(file.path.name)
            ns_root_file.path.ns_size = LogseqGraph._process_ns_size(ns_root_file)
            for key, value in ns_root_file.path.__dict__.items():
                if key.startswith("ns_") or key == "is_namespace":
                    setattr(ns_root_file, key, value)

        if ns_level <= 2:
            return ns_refs

        for ns_parent_file in index[ns_parent]:
            ns_parent_file: LogseqFile
            ns_parent_file.path.is_namespace = True
            ns_parent_file.path.ns_level = ns_level - 1
            ns_parent_file.path.ns_children.add(file.path.name)
            ns_parent_file.path.ns_size = LogseqGraph._process_ns_size(ns_parent_file)
            for key, value in ns_parent_file.path.__dict__.items():
                if key.startswith("ns_") or key == "is_namespace":
                    setattr(ns_parent_file, key, value)

        return ns_refs

    def process_summary_data(self, index: FileIndex) -> None:
        """Process summary data for each file based on metadata and content analysis."""
        unique_linked_references = self.unique_linked_references
        unique_linked_references_ns = self.unique_linked_references_ns
        for file in index:
            if not file.is_backlinked:
                file.is_backlinked = file.check_is_backlinked(unique_linked_references)
            if not file.is_backlinked_by_ns_only:
                file.is_backlinked_by_ns_only = file.check_is_backlinked(unique_linked_references_ns)
                if file.is_backlinked and file.is_backlinked_by_ns_only:
                    file.is_backlinked = False
            if file.file_type in ("journal", "page"):
                file.determine_node_type()

    def _process_dangling_links(self, all_file_names: set[str], unique_aliases: set[str]) -> list[str]:
        """Process dangling links in the graph."""
        unique_linked_references = self.unique_linked_references
        unique_linked_references_ns = self.unique_linked_references_ns
        all_linked_refs = unique_linked_references.union(unique_linked_references_ns)
        all_linked_refs.difference_update(all_file_names)
        all_linked_refs.difference_update(unique_aliases)
        dangling_links = sorted(get_not_builtin_properties(all_linked_refs))
        return dangling_links

    @staticmethod
    def _process_ns_size(file: LogseqFile) -> int:
        """
        Process the size of namespaces.

        Args:
            file (LogseqFile): The parent file to process.

        Returns:
            int: The size of the namespace.
        """
        if not file.path.ns_size:
            return len(file.path.ns_children)
        return file.path.ns_size + 1
