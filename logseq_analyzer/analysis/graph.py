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
    )

    _TO_NODE_TYPE = (FileTypes.JOURNAL.value, FileTypes.PAGE.value)

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
        all_linked_refs = self.all_linked_references
        linked_refs = self.unique_linked_references
        linked_refs_ns = self.unique_linked_references_ns
        unique_aliases = set()

        for file in index:
            if (curr_ns_info := file.path.ns_info) and file.path.is_namespace:
                linked_refs_ns.update(self.post_process_namespace(file, index))

            if not (f_data := file.data):
                continue

            found_aliases = f_data.get(Criteria.CON_ALIASES.value, [])
            unique_aliases.update(found_aliases)
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

            all_linked_refs = get_count_and_foundin_data(all_linked_refs, linked_references, file)

            if curr_ns_info and curr_ns_info.parent:
                linked_references.remove(curr_ns_info.parent)

            linked_refs.update(linked_references)

        all_linked_refs = LogseqGraph.sort_all_linked_references(all_linked_refs)
        dangling_links = self.process_dangling_links(index, unique_aliases)
        del unique_aliases
        self.dangling_links.extend(dangling_links)
        self.all_dangling_links = {k: v for k, v in all_linked_refs.items() if k in dangling_links}

    @staticmethod
    def sort_all_linked_references(all_linked_refs: dict) -> dict:
        """Sort all linked references by count and found_in."""
        for _, values in all_linked_refs.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        return sort_dict_by_value(all_linked_refs, value="count", reverse=True)

    def post_process_namespace(self, file: LogseqFile, index: "FileIndex") -> tuple[str, str]:
        """Post-process namespaces in the content data."""
        file_path = file.path
        if not (curr_ns_info := file_path.ns_info) or not file_path.is_namespace:
            return ("", file_path.name)

        ns_level = len(curr_ns_info.parts)
        ns_root = curr_ns_info.root
        ns_parent_full = curr_ns_info.parent_full
        ns_refs = (ns_root, file_path.name)

        for ns_root_file in index[ns_root]:
            ns_root_file: LogseqFile
            root_path = ns_root_file.path
            root_path.is_namespace = True
            root_path.ns_info.children.add(file_path.name)
            root_path.ns_info.size = len(root_path.ns_info.children)

        if ns_level <= 2:
            return ns_refs

        for ns_parent_file in index[ns_parent_full]:
            ns_parent_file: LogseqFile
            parent_path = ns_parent_file.path
            parent_path.ns_info.children.add(file_path.name)
            parent_path.ns_info.size = len(parent_path.ns_info.children)

        return ns_refs

    def process_summary_data(self, index: "FileIndex") -> None:
        """Process summary data for each file based on metadata and content analysis."""
        linked_refs = self.unique_linked_references
        linked_refs_ns = self.unique_linked_references_ns
        to_node_type = self._TO_NODE_TYPE
        for f in index:
            fnode = f.node
            fnode.backlinked = f.check_is_backlinked(linked_refs)
            fnode.backlinked_ns_only = f.check_is_backlinked(linked_refs_ns)
            if fnode.backlinked and fnode.backlinked_ns_only:
                fnode.backlinked = False
            if f.path.file_type in to_node_type:
                f.determine_node_type()

    def process_dangling_links(self, index: "FileIndex", unique_aliases: set[str]) -> list[str]:
        """Process dangling links in the graph."""
        all_file_names = (file.path.name for file in index)
        linked_refs = self.unique_linked_references
        linked_refs_ns = self.unique_linked_references_ns
        all_refs = linked_refs.union(linked_refs_ns)
        all_refs.difference_update(all_file_names, unique_aliases)
        return remove_builtin_properties(all_refs)

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
