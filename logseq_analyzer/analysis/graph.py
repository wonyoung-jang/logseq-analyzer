"""
This module contains functions for processing and analyzing Logseq graph data.
"""

from typing import TYPE_CHECKING, Any

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
            if f.is_namespace:
                self.unique_linked_refs_ns.update((f.ns_info.root, f.name))
                index.process_namespaces(f)
            if not f.data:
                continue
            found_aliases = f.data.get(Criteria.CON_ALIASES.value, [])
            self.unique_aliases.update(found_aliases)
            dataset = (
                found_aliases,
                f.data.get(Criteria.CON_DRAW.value, []),
                f.data.get(Criteria.CON_PAGE_REF.value, []),
                f.data.get(Criteria.CON_TAG.value, []),
                f.data.get(Criteria.CON_TAGGED_BACKLINK.value, []),
                f.data.get(Criteria.PROP_PAGE_BUILTIN.value, []),
                f.data.get(Criteria.PROP_PAGE_USER.value, []),
                f.data.get(Criteria.PROP_BLOCK_BUILTIN.value, []),
                f.data.get(Criteria.PROP_BLOCK_USER.value, []),
            )
            linked_references = []
            for data in dataset:
                if not data:
                    continue
                linked_references.extend(data)
            if f.ns_info.parent:
                lr_with_ns_parent = linked_references.copy() + [f.ns_info.parent]
                self.all_linked_refs = get_count_and_foundin_data(self.all_linked_refs, lr_with_ns_parent, f)
            else:
                self.all_linked_refs = get_count_and_foundin_data(self.all_linked_refs, linked_references, f)
            self.unique_linked_refs.update(linked_references)

    def sort_all_linked_references(self) -> dict:
        """Sort all linked references by count and found_in."""
        for _, values in self.all_linked_refs.items():
            values["found_in"] = sort_dict_by_value(values["found_in"], reverse=True)
        self.all_linked_refs = sort_dict_by_value(self.all_linked_refs, value="count", reverse=True)

    def post_process_summary(self, index: "FileIndex") -> None:
        """Process summary data for each file based on metadata and content analysis."""
        for f in index:
            f.node.check_backlinked(f.name, self.unique_linked_refs)
            f.node.check_backlinked_ns_only(f.name, self.unique_linked_refs_ns)
            if f.file_type in self._TO_NODE_TYPE:
                f.node.determine_node_type(f.has_content)

    def post_process_dangling(self, index: "FileIndex") -> list[str]:
        """Process dangling links in the graph."""
        all_file_names = (f.name for f in index)
        all_refs = self.unique_linked_refs.union(self.unique_linked_refs_ns)
        all_refs.difference_update(all_file_names, self.unique_aliases)
        self.dangling_links = remove_builtin_properties(all_refs)

    def post_process_all_dangling(self) -> None:
        """Process all dangling links to create a mapping of linked references."""
        self.all_dangling_links = {k: v for k, v in self.all_linked_refs.items() if k in self.dangling_links}

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
