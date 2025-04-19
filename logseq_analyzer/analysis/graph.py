"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from pathlib import Path

from ..io.cache import Cache
from ..logseq_file.file import LogseqFile
from ..utils.enums import Output, Criteria
from ..utils.helpers import singleton
from .index import FileIndex


@singleton
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    def __init__(self):
        """Initialize the LogseqGraph instance."""
        self.all_linked_references = {}
        self.dangling_links = set()
        self.index = FileIndex()
        self.unique_linked_references = set()
        self.unique_linked_references_ns = set()

    def process_graph_files(self):
        """Process all files in the Logseq graph folder."""
        for file_path in Cache().iter_modified_files():
            file = self.initialize_file(file_path)
            self.index.add(file)
            self.del_large_file_attributes(file)

    def initialize_file(self, file_path: Path) -> LogseqFile:
        """
        Initialize the file object.

        Args:
            file_path (Path): Path to the file to be initialized.

        Returns:
            LogseqFile: Initialized LogseqFile object.
        """
        file = LogseqFile(file_path)
        file.init_file_data()
        file.process_content_data()
        return file

    def del_large_file_attributes(self, file: LogseqFile):
        """
        Delete large attributes from the file object.

        Args:
            file (LogseqFile): The LogseqFile object to be modified.
        """
        delattr(file, "content_bullets")
        delattr(file, "content")
        delattr(file, "primary_bullet")

    def update_graph_files_with_cache(self):
        """Update the graph files with cached data."""
        cache = Cache()
        meta_data = cache.get("META_REPORTS", {})

        cached_files = meta_data.get("FileIndexFiles", [])
        cached_files = {file for file in cached_files if file not in self.index.files}
        self.index.files.update(cached_files)

        cached_hash_to_file_map = meta_data.get(Output.GRAPH_HASHED_FILES.value, {})
        cached_hash_to_file_map.update(self.index.hash_to_file)
        self.index.hash_to_file = cached_hash_to_file_map

        cached_dangling_links = meta_data.get(Output.DANGLING_LINKS.value, set())
        graph_dangling_links = {d for d in self.dangling_links if d not in cached_dangling_links}
        self.dangling_links = graph_dangling_links.union(cached_dangling_links)

    def post_processing_content(self):
        """Post-process the content data for all files."""
        unique_aliases = set()

        # Process each file's content
        for _, file in self.index.hash_to_file.items():
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
                self.all_linked_references.setdefault(item, {})
                self.all_linked_references[item]["count"] = self.all_linked_references[item].get("count", 0) + 1
                self.all_linked_references[item].setdefault("found_in", []).append(file.path.name)

            if hasattr(file, "ns_parent"):
                linked_references.remove(file.ns_parent)

            self.unique_linked_references.update(linked_references)

        self.all_linked_references = dict(
            sorted(
                self.all_linked_references.items(),
                key=lambda item: item[1]["count"],
                reverse=True,
            )
        )

        # Create dangling links
        all_linked_refs = self.unique_linked_references.union(self.unique_linked_references_ns)
        all_linked_refs.difference_update(self.index.name_to_files.keys())
        all_linked_refs.difference_update(unique_aliases)
        self.dangling_links = set(sorted(all_linked_refs))

    def post_processing_content_namespaces(self, file: LogseqFile):
        """Post-process namespaces in the content data."""
        ns_level = file.ns_level
        ns_root = file.ns_root
        ns_parent = file.ns_parent_full
        self.unique_linked_references_ns.update([ns_root, file.path.name])

        for ns_root_file in self.index.name_to_files.get(ns_root, []):
            ns_root_file.ns_level = 1
            if not hasattr(ns_root_file, "ns_children"):
                ns_root_file.ns_children = set()
            ns_root_file.ns_children.add(file.path.name)
            ns_root_file.ns_size = len(ns_root_file.ns_children)

        if ns_level <= 2:
            return

        for ns_parent_file in self.index.name_to_files.get(ns_parent, []):
            ns_parent_level = getattr(ns_parent_file, "ns_level", 0)
            direct_level = ns_level - 1
            ns_parent_file.ns_level = max(direct_level, ns_parent_level)
            if not hasattr(ns_parent_file, "ns_children"):
                ns_parent_file.ns_children = set()
            ns_parent_file.ns_children.add(file.path.name)
            ns_parent_file.ns_size = len(ns_parent_file.ns_children)

    def process_summary_data(self):
        """Process summary data for each file based on metadata and content analysis."""
        for file in self.index.files:
            file.is_backlinked = file.check_is_backlinked(self.unique_linked_references)
            file.is_backlinked_by_ns_only = file.check_is_backlinked(self.unique_linked_references_ns)
            if file.is_backlinked and file.is_backlinked_by_ns_only:
                file.is_backlinked = False
            if file.file_type in ("journal", "page"):
                file.node_type = file.determine_node_type()
