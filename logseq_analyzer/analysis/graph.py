"""Module with functions for processing and analyzing Logseq graph data."""

from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Any, ClassVar

from logseq_analyzer.utils.enums import CritContent, CritProp, FileType, Output
from logseq_analyzer.utils.helpers import (
    BUILT_IN_PROPERTIES,
    get_count_and_foundin_data,
    sort_dict_by_value,
)

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex
    from logseq_analyzer.logseq_file.file import LogseqFile


@dataclass(slots=True)
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    index: FileIndex
    all_linked_refs: dict[str, dict[str, dict]] = field(default_factory=dict)
    all_dangling_links: dict[str, dict[str, dict]] = field(default_factory=dict)
    dangling_links: set[str] = field(default_factory=set)
    linked_refs: set[str] = field(default_factory=set)
    linked_refs_ns: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)
    _TO_NODE_TYPE: ClassVar[frozenset[FileType]] = frozenset({FileType.JOURNAL, FileType.PAGE})

    def __post_init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.post_process_content()
        self.process_nodes()
        self.sort_all_linked_references()
        self.find_dangling_links()
        self.extract_all_dangling_link_data()

    def post_process_content(self) -> None:
        """Post-process the content data for all files."""
        for f in self.index:
            ns_info = f.info.namespace
            if ns_info.is_namespace:
                self.linked_refs_ns.update((ns_info.root, f.path.name))
                self.process_namespaces(f)
            if not (f_data := f.data):
                continue
            if found_aliases := f_data.get(CritContent.ALIASES, []):
                self.aliases.update(found_aliases)
            dataset = (
                found_aliases,
                f_data.get(CritContent.DRAW, []),
                f_data.get(CritContent.PAGE_REF, []),
                f_data.get(CritContent.TAG, []),
                f_data.get(CritContent.TAGGED_BACKLINK, []),
                f_data.get(CritProp.PAGE_BUILTIN, []),
                f_data.get(CritProp.PAGE_USER, []),
                f_data.get(CritProp.BLOCK_BUILTIN, []),
                f_data.get(CritProp.BLOCK_USER, []),
            )
            if not (linked_references := list(chain.from_iterable(dataset))):
                continue
            if ns_info.parent:
                lr_with_ns_parent = [*linked_references.copy(), ns_info.parent]
                self.all_linked_refs.update(
                    get_count_and_foundin_data(self.all_linked_refs, lr_with_ns_parent, f.path.name)
                )
            else:
                self.all_linked_refs.update(
                    get_count_and_foundin_data(self.all_linked_refs, linked_references, f.path.name)
                )
            self.linked_refs.update(linked_references)

    def process_namespaces(self, f: LogseqFile) -> None:
        """Post-process namespaces in the content data."""
        for ns_root_file in self.index[f.info.namespace.root]:
            ns_root_file: LogseqFile
            ns_info = ns_root_file.info.namespace
            if not ns_info.is_namespace:
                ns_info.is_namespace = True
            if f.path.name not in ns_info.children:
                ns_info.children.add(f.path.name)
        for ns_parent_file in self.index[f.info.namespace.parent_full]:
            ns_parent_file: LogseqFile
            ns_info = ns_parent_file.info.namespace
            if f.path.name not in ns_info.children:
                ns_info.children.add(f.path.name)

    def sort_all_linked_references(self) -> None:
        """Sort all linked references by count and found_in."""
        for values in self.all_linked_refs.values():
            found_in_map = values.get("found_in", {})
            values["found_in"] = sort_dict_by_value(found_in_map, reverse=True)
        self.all_linked_refs = sort_dict_by_value(self.all_linked_refs, value="count", reverse=True)

    def process_nodes(self) -> None:
        """Process summary data for each file based on metadata and content analysis."""
        for f in self.index:
            f.node.check_backlinked(f.path.name, self.linked_refs)
            f.node.check_backlinked_ns_only(f.path.name, self.linked_refs_ns)
            if f.path.file_type in LogseqGraph._TO_NODE_TYPE:
                f.node.determine_node_type(has_content=f.info.size.has_content)

    def find_dangling_links(self) -> None:
        """Process dangling links in the graph."""
        all_file_names = (f.path.name for f in self.index)
        all_refs = self.linked_refs.union(self.linked_refs_ns)
        all_refs.difference_update(all_file_names)
        all_refs.difference_update(self.aliases)
        self.dangling_links = all_refs.difference(BUILT_IN_PROPERTIES)

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
            Output.GRAPH_UNIQUE_ALIASES: self.aliases,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS: self.linked_refs_ns,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES: self.linked_refs,
        }
