"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from typing import TYPE_CHECKING, Any

from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria, FileTypes, Output
from ..utils.helpers import get_count_and_foundin_data, remove_builtin_properties, singleton, sort_dict_by_value

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
        "unique_aliases",
    )

    _TO_NODE_TYPE = (FileTypes.JOURNAL.value, FileTypes.PAGE.value)

    def __init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.all_linked_references: dict[str, dict[str, dict]] = {}
        self.all_dangling_links: dict[str, dict[str, dict]] = {}
        self.dangling_links: list[str] = []
        self.unique_linked_references: set[str] = set()
        self.unique_linked_references_ns: set[str] = set()
        self.unique_aliases: set[str] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqGraph instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqGraph instance."""
        return f"{self.__class__.__qualname__}"

    def process(self, index: "FileIndex") -> None:
        """Process the Logseq graph data."""
        self.post_process_content(index)
        self.post_process_summary(index)
        self.sort_all_linked_references()
        self.post_process_dangling(index)
        self.post_process_all_dangling()

    def post_process_content(self, index: "FileIndex") -> None:
        """Post-process the content data for all files."""
        for f in index:
            curr_ns_info = f.fname.ns_info
            if f.fname.is_namespace:
                self.unique_linked_references_ns.update(self.post_process_namespace(f, index))
            if not (f_data := f.data):
                continue
            found_aliases = f_data.get(Criteria.CON_ALIASES.value, [])
            self.unique_aliases.update(found_aliases)
            dataset = (
                found_aliases,
                f_data.get(Criteria.CON_DRAW.value, []),
                f_data.get(Criteria.CON_PAGE_REF.value, []),
                f_data.get(Criteria.CON_TAG.value, []),
                f_data.get(Criteria.CON_TAGGED_BACKLINK.value, []),
                f_data.get(Criteria.PROP_PAGE_BUILTIN.value, []),
                f_data.get(Criteria.PROP_PAGE_USER.value, []),
                f_data.get(Criteria.PROP_BLOCK_BUILTIN.value, []),
                f_data.get(Criteria.PROP_BLOCK_USER.value, []),
            )
            linked_references = []
            for data in dataset:
                if not data:
                    continue
                linked_references.extend(data)
            if curr_ns_info.parent:
                lr_with_ns_parent = linked_references.copy() + [curr_ns_info.parent]
                self.all_linked_references = get_count_and_foundin_data(
                    self.all_linked_references, lr_with_ns_parent, f
                )
            else:
                self.all_linked_references = get_count_and_foundin_data(
                    self.all_linked_references, linked_references, f
                )
            self.unique_linked_references.update(linked_references)

    def sort_all_linked_references(self) -> dict:
        """Sort all linked references by count and found_in."""
        for _, values in self.all_linked_references.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        self.all_linked_references = sort_dict_by_value(self.all_linked_references, value="count", reverse=True)

    @staticmethod
    def post_process_namespace(file: LogseqFile, index: "FileIndex") -> tuple[str, str]:
        """Post-process namespaces in the content data."""
        curr_ns_info = file.fname.ns_info
        ns_level = len(curr_ns_info.parts)
        ns_refs = (curr_ns_info.root, file.fname.name)

        for ns_root_f in index[curr_ns_info.root]:
            ns_root_f: LogseqFile
            ns_root_f.fname.is_namespace = True
            ns_root_f.fname.ns_info.children.add(file.fname.name)
            ns_root_f.fname.ns_info.size = len(ns_root_f.fname.ns_info.children)

        if ns_level <= 2:
            return ns_refs

        for ns_parent_f in index[curr_ns_info.parent_full]:
            ns_parent_f: LogseqFile
            ns_parent_f.fname.ns_info.children.add(file.fname.name)
            ns_parent_f.fname.ns_info.size = len(ns_parent_f.fname.ns_info.children)

        return ns_refs

    def post_process_summary(self, index: "FileIndex") -> None:
        """Process summary data for each file based on metadata and content analysis."""
        for f in index:
            f.node.backlinked = f.check_is_backlinked(self.unique_linked_references)
            f.node.backlinked_ns_only = f.check_is_backlinked(self.unique_linked_references_ns)
            if f.node.backlinked and f.node.backlinked_ns_only:
                f.node.backlinked = False
            if f.fname.file_type in self._TO_NODE_TYPE:
                f.determine_node_type()

    def post_process_dangling(self, index: "FileIndex") -> list[str]:
        """Process dangling links in the graph."""
        all_file_names = (f.fname.name for f in index)
        all_refs = self.unique_linked_references.union(self.unique_linked_references_ns)
        all_refs.difference_update(all_file_names, self.unique_aliases)
        self.dangling_links = remove_builtin_properties(all_refs)

    def post_process_all_dangling(self) -> None:
        """Process all dangling links to create a mapping of linked references."""
        self.all_dangling_links = {k: v for k, v in self.all_linked_references.items() if k in self.dangling_links}

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the graph analysis."""
        return {
            Output.GRAPH_ALL_LINKED_REFERENCES.value: self.all_linked_references,
            Output.GRAPH_ALL_DANGLING_LINKS.value: self.all_dangling_links,
            Output.GRAPH_DANGLING_LINKS.value: self.dangling_links,
            Output.GRAPH_UNIQUE_ALIASES.value: self.unique_aliases,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS.value: self.unique_linked_references_ns,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES.value: self.unique_linked_references,
        }
