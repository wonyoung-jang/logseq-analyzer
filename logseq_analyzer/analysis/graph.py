"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from typing import Any

from ..utils.enums import Criteria, FileTypes, Output
from ..utils.helpers import get_count_and_foundin_data, remove_builtin_properties, sort_dict_by_value
from .index import FileIndex

__all__ = [
    "LogseqGraph",
]


class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    __slots__ = (
        "all_linked_refs",
        "all_dangling_links",
        "dangling_links",
        "unique_linked_refs",
        "unique_linked_refs_ns",
        "unique_aliases",
    )

    _TO_NODE_TYPE: frozenset[str] = frozenset({FileTypes.JOURNAL.value, FileTypes.PAGE.value})

    def __init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.all_linked_refs: dict[str, dict[str, dict]] = {}
        self.all_dangling_links: dict[str, dict[str, dict]] = {}
        self.dangling_links: list[str] = []
        self.unique_linked_refs: set[str] = set()
        self.unique_linked_refs_ns: set[str] = set()
        self.unique_aliases: set[str] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqGraph instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqGraph instance."""
        return f"{self.__class__.__qualname__}"

    def process(self, index: FileIndex) -> None:
        """Process the Logseq graph data."""
        self.post_process_content(index)
        self.post_process_summary(index)
        self.sort_all_linked_references()
        self.post_process_dangling(index)
        self.post_process_all_dangling()

    def post_process_content(self, index: FileIndex) -> None:
        """Post-process the content data for all files."""
        all_linked_refs = self.all_linked_refs
        unique_linked_refs = self.unique_linked_refs
        unique_linked_refs_ns = self.unique_linked_refs_ns
        unique_aliases = self.unique_aliases

        for f in index:
            ns_info = f.ns_info
            if f.is_namespace:
                unique_linked_refs_ns.update((ns_info.root, f.name))
                index.process_namespaces(f)
            if not f.data:
                continue
            get_data = f.data.get
            found_aliases = get_data(Criteria.CON_ALIASES.value, [])
            unique_aliases.update(found_aliases)
            dataset = (
                found_aliases,
                get_data(Criteria.CON_DRAW.value, []),
                get_data(Criteria.CON_PAGE_REF.value, []),
                get_data(Criteria.CON_TAG.value, []),
                get_data(Criteria.CON_TAGGED_BACKLINK.value, []),
                get_data(Criteria.PROP_PAGE_BUILTIN.value, []),
                get_data(Criteria.PROP_PAGE_USER.value, []),
                get_data(Criteria.PROP_BLOCK_BUILTIN.value, []),
                get_data(Criteria.PROP_BLOCK_USER.value, []),
            )
            linked_references = [d for data in dataset for d in data if data]
            if ns_info.parent:
                lr_with_ns_parent = linked_references.copy() + [ns_info.parent]
                all_linked_refs = get_count_and_foundin_data(all_linked_refs, lr_with_ns_parent, f)
            else:
                all_linked_refs = get_count_and_foundin_data(all_linked_refs, linked_references, f)
            unique_linked_refs.update(linked_references)

    def sort_all_linked_references(self) -> dict:
        """Sort all linked references by count and found_in."""
        all_linked_refs = self.all_linked_refs
        for _, values in all_linked_refs.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        all_linked_refs = sort_dict_by_value(all_linked_refs, value="count", reverse=True)

    def post_process_summary(self, index: FileIndex) -> None:
        """Process summary data for each file based on metadata and content analysis."""
        unique_linked_refs = self.unique_linked_refs
        unique_linked_refs_ns = self.unique_linked_refs_ns
        check_for_nodes = LogseqGraph._TO_NODE_TYPE
        for f in index:
            f.node.check_backlinked(f.name, unique_linked_refs)
            f.node.check_backlinked_ns_only(f.name, unique_linked_refs_ns)
            if f.file_type in check_for_nodes:
                f.node.determine_node_type(f.has_content)

    def post_process_dangling(self, index: FileIndex) -> list[str]:
        """Process dangling links in the graph."""
        unique_linked_refs = self.unique_linked_refs
        unique_linked_refs_ns = self.unique_linked_refs_ns
        unique_aliases = self.unique_aliases
        all_file_names = (f.name for f in index)
        all_refs = unique_linked_refs.union(unique_linked_refs_ns)
        all_refs.difference_update(all_file_names, unique_aliases)
        self.dangling_links.extend(remove_builtin_properties(all_refs))

    def post_process_all_dangling(self) -> None:
        """Process all dangling links to create a mapping of linked references."""
        all_linked_refs = self.all_linked_refs
        dangling_links = self.dangling_links
        self.all_dangling_links.update({k: v for k, v in all_linked_refs.items() if k in dangling_links})

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the graph analysis."""
        return {
            Output.GRAPH_ALL_LINKED_REFERENCES.value: self.all_linked_refs,
            Output.GRAPH_ALL_DANGLING_LINKS.value: self.all_dangling_links,
            Output.GRAPH_DANGLING_LINKS.value: self.dangling_links,
            Output.GRAPH_UNIQUE_ALIASES.value: self.unique_aliases,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS.value: self.unique_linked_refs_ns,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES.value: self.unique_linked_refs,
        }
