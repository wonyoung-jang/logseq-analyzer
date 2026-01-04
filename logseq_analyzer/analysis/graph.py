"""Module with functions for processing and analyzing Logseq graph data."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Any, ClassVar

from ..utils.enums import CritContent, CritProp, FileType, Output
from ..utils.helpers import get_count_and_foundin_data, remove_builtin_properties, sort_dict_by_value

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile
    from .index import FileIndex

__all__ = [
    "LogseqGraph",
]


@dataclass(slots=True)
class UniqueSets:
    """Dataclass to hold unique sets for linked references and aliases."""

    linked_refs: set[str] = field(default_factory=set)
    linked_refs_ns: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)


@dataclass(slots=True)
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    index: FileIndex
    all_linked_refs: dict[str, dict[str, dict]] = field(default_factory=dict)
    all_dangling_links: dict[str, dict[str, dict]] = field(default_factory=dict)
    dangling_links: set[str] = field(default_factory=set)
    unique: UniqueSets = field(default_factory=UniqueSets)

    _TO_NODE_TYPE: ClassVar[frozenset[FileType]] = frozenset({FileType.JOURNAL, FileType.PAGE})

    def __post_init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.process()

    def process(self) -> None:
        """Process the Logseq graph data."""
        self.post_process_content()
        self.process_nodes()
        self.sort_all_linked_references()
        self.find_dangling_links()
        self.extract_all_dangling_link_data()

    def post_process_content(self) -> None:
        """Post-process the content data for all files."""
        all_linked_refs = self.all_linked_refs
        update_unique_linked_refs = self.unique.linked_refs.update
        update_unique_linked_refs_ns = self.unique.linked_refs_ns.update
        update_unique_aliases = self.unique.aliases.update
        process_namespaces = self.process_namespaces

        for f in self.index:
            ns_info = f.info.namespace
            if ns_info.is_namespace:
                update_unique_linked_refs_ns((ns_info.root, f.path.name))
                process_namespaces(f)

            if not (f_data := f.data):
                continue

            get_data = f_data.get
            if found_aliases := get_data(CritContent.ALIASES, []):
                update_unique_aliases(found_aliases)

            dataset = (
                found_aliases,
                get_data(CritContent.DRAW, []),
                get_data(CritContent.PAGE_REF, []),
                get_data(CritContent.TAG, []),
                get_data(CritContent.TAGGED_BACKLINK, []),
                get_data(CritProp.PAGE_BUILTIN, []),
                get_data(CritProp.PAGE_USER, []),
                get_data(CritProp.BLOCK_BUILTIN, []),
                get_data(CritProp.BLOCK_USER, []),
            )
            if not (linked_references := list(chain.from_iterable(dataset))):
                continue

            if ns_info.parent:
                lr_with_ns_parent = [*linked_references.copy(), ns_info.parent]
                all_linked_refs.update(get_count_and_foundin_data(all_linked_refs, lr_with_ns_parent, f.path.name))
            else:
                all_linked_refs.update(get_count_and_foundin_data(all_linked_refs, linked_references, f.path.name))

            update_unique_linked_refs(linked_references)

    def process_namespaces(self, f: LogseqFile) -> None:
        """Post-process namespaces in the content data."""
        index = self.index
        filename = f.path.name
        curr_ns_info = f.info.namespace
        for ns_root_file in index[curr_ns_info.root]:
            ns_root_file: LogseqFile
            ns_info = ns_root_file.info.namespace
            if not ns_info.is_namespace:
                ns_info.is_namespace = True
            if filename not in ns_info.children:
                ns_info.children.add(filename)

        for ns_parent_file in index[curr_ns_info.parent_full]:
            ns_parent_file: LogseqFile
            ns_info = ns_parent_file.info.namespace
            if filename not in ns_info.children:
                ns_info.children.add(filename)

    def sort_all_linked_references(self) -> None:
        """Sort all linked references by count and found_in."""
        for values in self.all_linked_refs.values():
            found_in_map = values.get("found_in", {})
            values["found_in"] = sort_dict_by_value(found_in_map, reverse=True)

        self.all_linked_refs = sort_dict_by_value(self.all_linked_refs, value="count", reverse=True)

    def process_nodes(self) -> None:
        """Process summary data for each file based on metadata and content analysis."""
        unique_refs = self.unique.linked_refs
        unique_refs_ns = self.unique.linked_refs_ns
        check_for_nodes = LogseqGraph._TO_NODE_TYPE
        for f in self.index:
            f_path = f.path
            filename = f_path.name
            node = f.node
            node.check_backlinked(filename, unique_refs)
            node.check_backlinked_ns_only(filename, unique_refs_ns)
            if f_path.file_type in check_for_nodes:
                node.determine_node_type(has_content=f.info.size.has_content)

    def find_dangling_links(self) -> None:
        """Process dangling links in the graph."""
        all_file_names = (f.path.name for f in self.index)

        all_refs = self.unique.linked_refs.union(self.unique.linked_refs_ns)
        all_refs.difference_update(all_file_names)
        all_refs.difference_update(self.unique.aliases)

        self.dangling_links = remove_builtin_properties(all_refs)

    def extract_all_dangling_link_data(self) -> None:
        """Process all dangling links to create a mapping of linked references."""
        self.all_dangling_links = {k: v for k, v in self.all_linked_refs.items() if k in self.dangling_links}

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the graph analysis."""
        return {
            Output.GRAPH_ALL_LINKED_REFERENCES: self.all_linked_refs,
            Output.GRAPH_ALL_DANGLING_LINKS: self.all_dangling_links,
            Output.GRAPH_DANGLING_LINKS: self.dangling_links,
            Output.GRAPH_UNIQUE_ALIASES: self.unique.aliases,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS: self.unique.linked_refs_ns,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES: self.unique.linked_refs,
        }
