"""Module with functions for processing and analyzing Logseq graph data."""

from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING

from logseq_analyzer.utils.enums import Crit, FileType, Output, OutputDir
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES, get_count_and_foundin_data, sort_dict_by_value

if TYPE_CHECKING:
    from logseq_analyzer.domain.file import LogseqFile
    from logseq_analyzer.domain.index import FileIndex

_TO_NODE_TYPE = frozenset((FileType.JOURNAL, FileType.PAGE))


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
        self.process()
        self.process_nodes()
        self.sort_all_linked_references()
        self.process_dangling()

    def process(self) -> None:
        """Post-process the content data for all files."""
        for f in self.index:
            self._post_process_content(f)

    def _post_process_content(self, f: LogseqFile) -> None:
        if f.info.namespace.is_namespace:
            self.linked_refs_ns.update((f.info.namespace.root, f.path.name))
            self.process_namespaces(f)
        if not (f_data := f.data):
            return
        if _aliases := f_data.get(Crit.Content.ALIASES, []):
            self.aliases.update(_aliases)
        _dataset = (
            _aliases,
            f_data.get(Crit.Content.DRAW, []),
            f_data.get(Crit.Content.PAGE_REF, []),
            f_data.get(Crit.Content.TAG, []),
            f_data.get(Crit.Content.TAGGED_BACKLINK, []),
            f_data.get(Crit.Prop.PAGE_BUILTIN, []),
            f_data.get(Crit.Prop.PAGE_USER, []),
            f_data.get(Crit.Prop.BLOCK_BUILTIN, []),
            f_data.get(Crit.Prop.BLOCK_USER, []),
        )
        if not (_linkedrefs := list(chain.from_iterable(_dataset))):
            return
        if f.info.namespace.parent:
            lr_with_ns_parent = [*_linkedrefs, f.info.namespace.parent]
            self.all_linked_refs = get_count_and_foundin_data(self.all_linked_refs, lr_with_ns_parent, f.path.name)
        else:
            self.all_linked_refs = get_count_and_foundin_data(self.all_linked_refs, _linkedrefs, f.path.name)
        self.linked_refs.update(_linkedrefs)

    def process_namespaces(self, f: LogseqFile) -> None:
        """Post-process namespaces in the content data."""
        for _root in self.index.get_from_name(f.info.namespace.root):
            _root.info.namespace.is_namespace = True
            _root.info.namespace.children.add(f.path.name)
        for _parent in self.index.get_from_name(f.info.namespace.parent_full):
            _parent.info.namespace.children.add(f.path.name)

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
        if f.path.name in self.linked_refs:
            self.linked_refs.remove(f.path.name)
            f.node.backlinked = True
        if f.path.name in self.linked_refs_ns:
            self.linked_refs_ns.remove(f.path.name)
            if not f.node.backlinked_ns_only:
                f.node.backlinked_ns_only = True
                f.node.backlinked = False
        if f.path.file_type in _TO_NODE_TYPE:
            f.node.determine_node_type(has_content=f.info.size.has_content)

    def process_dangling(self) -> None:
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
            OutputDir.GRAPH: {
                Output.GRAPH_ALL_LINKED_REFERENCES: self.all_linked_refs,
                Output.GRAPH_ALL_DANGLING_LINKS: self.all_dangling_links,
                Output.GRAPH_DANGLING_LINKS: self.dangling_links,
                Output.GRAPH_UNIQUE_ALIASES: self.aliases,
                Output.GRAPH_UNIQUE_LINKED_REFERENCES_NS: self.linked_refs_ns,
                Output.GRAPH_UNIQUE_LINKED_REFERENCES: self.linked_refs,
            }
        }
