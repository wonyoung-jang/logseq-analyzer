"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from typing import TYPE_CHECKING, Any

from ..config.builtin_properties import get_user_properties
from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria, FileTypes, Output
from ..utils.helpers import get_count_and_foundin_data, singleton, sort_dict_by_value

if TYPE_CHECKING:
    from .index import FileIndex


__all__ = [
    "LogseqGraph",
]


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
        self.all_linked_references: dict[str, dict[str, dict]] = {}
        self.all_dangling_links: dict[str, dict[str, dict]] = {}
        self.dangling_links: list[str] = []
        self.unique_linked_references: set[str] = set()
        self.unique_linked_references_ns: set[str] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqGraph instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqGraph instance."""
        return f"{self.__class__.__qualname__}"

    def post_processing_content(self, index: "FileIndex") -> None:
        """Post-process the content data for all files."""
        all_linked_references = self.all_linked_references
        unique_aliases = set()
        unique_linked_references = self.unique_linked_references
        unique_linked_references_ns = self.unique_linked_references_ns
        for file in index:
            if (curr_ns_info := file.path.ns_info) and file.path.is_namespace:
                ns_refs = self.post_processing_content_namespaces(file, index)
                unique_linked_references_ns.update(ns_refs)
            found_aliases = file.data.get(Criteria.ALIASES.value, [])
            unique_aliases.update(found_aliases)
            linked_references = [
                found_aliases,
                file.data.get(Criteria.DRAWS.value, []),
                file.data.get(Criteria.PAGE_REFERENCES.value, []),
                file.data.get(Criteria.TAGS.value, []),
                file.data.get(Criteria.TAGGED_BACKLINKS.value, []),
                file.data.get(Criteria.PROP_PAGE_BUILTIN.value, []),
                file.data.get(Criteria.PROP_PAGE_USER.value, []),
                file.data.get(Criteria.PROP_BLOCK_BUILTIN.value, []),
                file.data.get(Criteria.PROP_BLOCK_USER.value, []),
            ]
            linked_references: list[str] = [item for sublist in linked_references for item in sublist if item]
            if curr_ns_info:
                linked_references.append(curr_ns_info.parent)

            get_count_and_foundin_data(all_linked_references, linked_references, file)

            if curr_ns_info and curr_ns_info.parent:
                linked_references.remove(curr_ns_info.parent)
            unique_linked_references.update(linked_references)
        for _, values in all_linked_references.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        all_linked_references = sort_dict_by_value(all_linked_references, value="count", reverse=True)
        all_file_names = (file.path.name for file in index)
        dangling_links = self.process_dangling_links(all_file_names, unique_aliases)
        self.dangling_links = dangling_links
        self.all_dangling_links = {k: v for k, v in all_linked_references.items() if k in dangling_links}

    def post_processing_content_namespaces(self, file: LogseqFile, index: "FileIndex") -> tuple[str, str]:
        """Post-process namespaces in the content data."""
        if not (curr_ns_info := file.path.ns_info) or not file.path.is_namespace:
            return ("", file.path.name)

        ns_level = len(curr_ns_info.parts)
        ns_root = curr_ns_info.root
        ns_parent_full = curr_ns_info.parent_full
        ns_refs = (ns_root, file.path.name)

        for ns_root_file in index[ns_root]:
            ns_root_file: LogseqFile
            if not ns_root_file.path.is_namespace:
                ns_root_file.path.is_namespace = True
            ns_root_file.path.ns_info.children.add(file.path.name)
            ns_root_file.path.ns_info.size = len(ns_root_file.path.ns_info.children)
            ns_root_file.set_ns_data()

        if ns_level <= 2:
            return ns_refs

        for ns_parent_file in index[ns_parent_full]:
            ns_parent_file: LogseqFile
            ns_parent_file.path.ns_info.children.add(file.path.name)
            ns_parent_file.path.ns_info.size = len(ns_parent_file.path.ns_info.children)
            ns_parent_file.set_ns_data()

        return ns_refs

    def process_summary_data(self, index: "FileIndex") -> None:
        """Process summary data for each file based on metadata and content analysis."""
        unique_linked_references = self.unique_linked_references
        unique_linked_references_ns = self.unique_linked_references_ns
        for file in index:
            fn = file.node
            if not fn.is_backlinked:
                fn.is_backlinked = file.check_is_backlinked(unique_linked_references)
            if not fn.is_backlinked_by_ns_only:
                fn.is_backlinked_by_ns_only = file.check_is_backlinked(unique_linked_references_ns)
                if fn.is_backlinked and fn.is_backlinked_by_ns_only:
                    fn.is_backlinked = False
            if file.path.file_type in (FileTypes.JOURNAL.value, FileTypes.PAGE.value):
                file.determine_node_type()

    def process_dangling_links(self, all_file_names: set[str], unique_aliases: set[str]) -> list[str]:
        """Process dangling links in the graph."""
        linked_refs = self.unique_linked_references
        linked_refs_ns = self.unique_linked_references_ns
        all_refs = linked_refs.union(linked_refs_ns)
        all_refs.difference_update(all_file_names)
        all_refs.difference_update(unique_aliases)
        return sorted(get_user_properties(all_refs))

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the graph analysis."""
        return {
            Output.ALL_LINKED_REFERENCES.value: self.all_linked_references,
            Output.ALL_DANGLING_LINKS.value: self.all_dangling_links,
            Output.DANGLING_LINKS.value: self.dangling_links,
            Output.UNIQUE_LINKED_REFERENCES_NS.value: self.unique_linked_references_ns,
            Output.UNIQUE_LINKED_REFERENCES.value: self.unique_linked_references,
        }
