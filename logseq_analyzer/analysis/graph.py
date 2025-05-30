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
        "_unique_aliases",
    )

    _TO_NODE_TYPE = (FileTypes.JOURNAL.value, FileTypes.PAGE.value)

    def __init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.all_linked_references: dict[str, dict[str, dict]] = {}
        self.all_dangling_links: dict[str, dict[str, dict]] = {}
        self.dangling_links: list[str] = []
        self.unique_linked_references: set[str] = set()
        self.unique_linked_references_ns: set[str] = set()
        self._unique_aliases: set[str] = set()

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
            if (curr_ns_info := f.filename.ns_info) and f.filename.is_namespace:
                self.unique_linked_references_ns.update(self.post_process_namespace(f, index))
            if not (f_data := f.data):
                continue
            found_aliases = f_data.get(Criteria.CON_ALIASES.value, [])
            self._unique_aliases.update(found_aliases)
            linked_references = [
                found_aliases,
                f_data.get(Criteria.CON_DRAW.value, []),
                f_data.get(Criteria.CON_PAGE_REF.value, []),
                f_data.get(Criteria.CON_TAG.value, []),
                f_data.get(Criteria.CON_TAGGED_BACKLINK.value, []),
                f_data.get(Criteria.PROP_PAGE_BUILTIN.value, []),
                f_data.get(Criteria.PROP_PAGE_USER.value, []),
                f_data.get(Criteria.PROP_BLOCK_BUILTIN.value, []),
                f_data.get(Criteria.PROP_BLOCK_USER.value, []),
            ]
            linked_references: list[str] = [item for sublist in linked_references for item in sublist if item]
            if curr_ns_info:
                linked_references.append(curr_ns_info.parent)
            self.all_linked_references = get_count_and_foundin_data(self.all_linked_references, linked_references, f)
            if curr_ns_info and curr_ns_info.parent:
                linked_references.remove(curr_ns_info.parent)
            self.unique_linked_references.update(linked_references)

    def sort_all_linked_references(self) -> dict:
        """Sort all linked references by count and found_in."""
        for _, values in self.all_linked_references.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        self.all_linked_references = sort_dict_by_value(self.all_linked_references, value="count", reverse=True)

    @staticmethod
    def post_process_namespace(file: LogseqFile, index: "FileIndex") -> tuple[str, str]:
        """Post-process namespaces in the content data."""
        file_path = file.filename
        if not (curr_ns_info := file_path.ns_info) or not file_path.is_namespace:
            return ("", file_path.name)

        ns_level = len(curr_ns_info.parts)
        ns_root = curr_ns_info.root
        ns_parent_full = curr_ns_info.parent_full
        ns_refs = (ns_root, file_path.name)

        for ns_root_file in index[ns_root]:
            ns_root_file: LogseqFile
            root_path = ns_root_file.filename
            root_path.is_namespace = True
            root_path.ns_info.children.add(file_path.name)
            root_path.ns_info.size = len(root_path.ns_info.children)

        if ns_level <= 2:
            return ns_refs

        for ns_parent_file in index[ns_parent_full]:
            ns_parent_file: LogseqFile
            parent_path = ns_parent_file.filename
            parent_path.ns_info.children.add(file_path.name)
            parent_path.ns_info.size = len(parent_path.ns_info.children)

        return ns_refs

    def post_process_summary(self, index: "FileIndex") -> None:
        """Process summary data for each file based on metadata and content analysis."""
        for f in index:
            f_node = f.node
            f_node.backlinked = f.check_is_backlinked(self.unique_linked_references)
            f_node.backlinked_ns_only = f.check_is_backlinked(self.unique_linked_references_ns)
            if f_node.backlinked and f_node.backlinked_ns_only:
                f_node.backlinked = False
            if f.filename.file_type in self._TO_NODE_TYPE:
                f.determine_node_type()

    def post_process_dangling(self, index: "FileIndex") -> list[str]:
        """Process dangling links in the graph."""
        all_file_names = (file.filename.name for file in index)
        all_refs = self.unique_linked_references.union(self.unique_linked_references_ns)
        all_refs.difference_update(all_file_names, self._unique_aliases)
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
            Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS.value: self.unique_linked_references_ns,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES.value: self.unique_linked_references,
        }
