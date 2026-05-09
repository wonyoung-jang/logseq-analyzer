"""Module with functions for processing and analyzing Logseq graph data."""

from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

from logseq_analyzer.utils.enums import Crit, CritProp, FileType, Output
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES, get_count_and_foundin_data, sort_dict_by_value

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex
    from logseq_analyzer.logseq_file.file import LogseqFile

_TO_NODE_TYPE = frozenset({FileType.JOURNAL, FileType.PAGE})


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

    def __post_init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        self.post_process_content()
        self.process_nodes()
        self.sort_all_linked_references()
        self.process_dangling_links()

    def post_process_content(self) -> None:
        """Post-process the content data for all files."""
        for f in self.index:
            self._post_process_content(f)

    def _post_process_content(self, f: LogseqFile) -> None:
        ns_info = f.info.namespace
        if ns_info.is_namespace:
            self.linked_refs_ns.update((ns_info.root, f.path.name))
            self.process_namespaces(f)
        if not (f_data := f.data):
            return
        if found_aliases := f_data.get(Crit.Content.ALIASES, []):
            self.aliases.update(found_aliases)
        dataset = (
            found_aliases,
            f_data.get(Crit.Content.DRAW, []),
            f_data.get(Crit.Content.PAGE_REF, []),
            f_data.get(Crit.Content.TAG, []),
            f_data.get(Crit.Content.TAGGED_BACKLINK, []),
            f_data.get(CritProp.PAGE_BUILTIN, []),
            f_data.get(CritProp.PAGE_USER, []),
            f_data.get(CritProp.BLOCK_BUILTIN, []),
            f_data.get(CritProp.BLOCK_USER, []),
        )
        if not (linked_references := list(chain.from_iterable(dataset))):
            return
        if ns_info.parent:
            lr_with_ns_parent = [*linked_references, ns_info.parent]
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
        ns_roots = self.index[f.info.namespace.root]
        if isinstance(ns_roots, list):
            for ns_root_file in ns_roots:
                ns_info = ns_root_file.info.namespace
                if not ns_info.is_namespace:
                    ns_info.is_namespace = True
                if f.path.name not in ns_info.children:
                    ns_info.children.add(f.path.name)
        ns_parents = self.index[f.info.namespace.parent_full]
        if isinstance(ns_parents, list):
            for ns_parent_file in ns_parents:
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
            self._process_nodes(f)

    def _process_nodes(self, f: LogseqFile) -> None:
        """Process summary data for a single file based on metadata and content analysis."""
        f.node.check_backlinked(f.path.name, self.linked_refs)
        f.node.check_backlinked_ns_only(f.path.name, self.linked_refs_ns)
        if f.path.file_type in _TO_NODE_TYPE:
            f.node.determine_node_type(has_content=f.info.size.has_content)

    def process_dangling_links(self) -> None:
        """Process dangling links in the graph."""
        self.dangling_links = (
            (self.linked_refs | self.linked_refs_ns)
            - set(self.index.yield_names())
            - self.aliases
            - BUILT_IN_PROPERTIES
        )
        self.all_dangling_links = {k: v for k, v in self.all_linked_refs.items() if k in self.dangling_links}

    @property
    def report(self) -> dict[str, object]:
        """Generate a report of the graph analysis."""
        return {
            Output.GRAPH_ALL_LINKED_REFERENCES: self.all_linked_refs,
            Output.GRAPH_ALL_DANGLING_LINKS: self.all_dangling_links,
            Output.GRAPH_DANGLING_LINKS: self.dangling_links,
            Output.GRAPH_UNIQUE_ALIASES: self.aliases,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS: self.linked_refs_ns,
            Output.GRAPH_UNIQUE_LINKED_REFERENCES: self.linked_refs,
        }
