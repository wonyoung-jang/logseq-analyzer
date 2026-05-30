"""Module for analyzing Logseq graph data.

Namespaces:
    What are the problems trying to be solved?
        Logseq's move to a database system from a markdown one.
        Currently, namespace pages are full and valid, so root/parent/child is a name.
        The proposed migration by Logseq is to split each part and tag the children with their parents.
        Now we have three pages of root, parent, and child.
    Problems:
        1. The split namespace parts may conflict with existing, non-namespace pages.
        2. Some parents may appear across multiple namespaces at different depths.
        3. There is no easy way to get data about namespaces.
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from itertools import chain
from typing import TYPE_CHECKING

from logseq_analyzer.domain.model import LOGSEQ_BUILTIN_PROPERTY, FileType, LogseqNode
from logseq_analyzer.domain.patterns import DT_ORDINAL_PATTERN, Crit, CriteriaGroup

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


logger = logging.getLogger(__name__)


type _NsTree = dict[str, _NsTree]


def _defdict_list() -> defaultdict:
    return defaultdict(list)


def _defdict_set() -> defaultdict:
    return defaultdict(set)


def _update_counts(result: dict, collection: Iterable[str], filename: str) -> None:
    """Update the result dictionary with counts and file occurrences."""
    for item in collection:
        entry = result.setdefault(item, {"count": 0, "found_in": Counter()})
        entry["count"] += 1
        entry["found_in"][filename] += 1


def get_dangling(linkedrefs: set[str], names: set[str], aliases: set[str]) -> set[str]:
    """Get the set of dangling links from a given set of names."""
    return ((linkedrefs - names) - aliases) - LOGSEQ_BUILTIN_PROPERTY


def process_journal(journals: set[str], dangling: set[str], jrnlfmt_page: str) -> dict[str, list[datetime]]:
    """Build a complete timeline of journal entries, filling in any missing dates."""

    def _name_to_dt(names: Iterable[str]) -> Iterator[datetime]:
        for name in names:
            n = DT_ORDINAL_PATTERN.sub("", name)
            try:
                yield datetime.strptime(n, jrnlfmt_page).replace(tzinfo=UTC)
            except ValueError:
                continue

    d = defaultdict(list)
    d["existing"].extend(sorted(_name_to_dt(journals)))
    d["dangling"].extend(sorted(_name_to_dt(dangling)))
    dangling_set = set(d["dangling"])
    existing = d["existing"]
    n_existing = len(existing)
    for i, date in enumerate(existing, start=1):
        _expected = date + timedelta(days=1)
        while i < n_existing and _expected < existing[i]:
            if _expected not in dangling_set:
                d["missing"].append(_expected)
            _expected = _expected + timedelta(days=1)
    return d


def get_asset_to_backlink(asset_to_link: set[LogseqNode], asset_mention: set[str]) -> Iterator[LogseqNode]:
    """Get the assets that need to be backlinked based on the index."""
    yield from (n for n in asset_to_link if n.name in asset_mention or any(n.name in m for m in asset_mention))


@dataclass(slots=True)
class AnalysisInput:
    """Class to represent the input for Logseq analysis."""

    aliases: set[str] = field(default_factory=set)
    linkedref: set[str] = field(default_factory=set)
    linkedref_ns: set[str] = field(default_factory=set)
    to_mark_ns: set[str] = field(default_factory=set)
    journal_names: set[str] = field(default_factory=set)
    asset_to_link: set[LogseqNode] = field(default_factory=set)
    asset_mention: set[str] = field(default_factory=set)

    def collect_input_data(self, n: LogseqNode) -> None:
        """Process a file to find linked references and aliases."""
        self.aliases.update(n.get_data(Crit.Content.ALIAS))
        self.linkedref.update(chain.from_iterable(n.get_data(key) for key in CriteriaGroup.BACKLINK.value))
        self.asset_mention.update(chain.from_iterable(n.get_data(key) for key in CriteriaGroup.ASSETMENTION.value))
        if n.is_ns:
            self.to_mark_ns.add(n.ns_root)
            self.linkedref_ns.update({n.name, n.ns_root, n.ns_parent})
        if n.filetype == FileType.ASSET:
            self.asset_to_link.add(n)
        if n.filetype == FileType.JOURNAL:
            self.journal_names.add(n.name)


@dataclass(slots=True)
class PreWrite:
    """Class to represent the input for Logseq analysis."""

    graph_to_link: set[LogseqNode] = field(default_factory=set)
    graph_to_link_ns: set[LogseqNode] = field(default_factory=set)
    graph_to_ns: set[LogseqNode] = field(default_factory=set)

    def collect_prewrite_data(
        self, n: LogseqNode, linkedref: set[str], linkedref_ns: set[str], to_mark_ns: set[str]
    ) -> None:
        """Process a file to find linked references and aliases."""
        if n.name in linkedref:
            self.graph_to_link.add(n)
        if n.name in linkedref_ns:
            self.graph_to_link_ns.add(n)
        if n.name in to_mark_ns and not n.is_ns:
            self.graph_to_ns.add(n)


@dataclass(slots=True)
class PostWrite:
    """Class to represent the post-write processing for Logseq analysis."""

    names: set[str] = field(default_factory=set)
    non_ns_names: set[str] = field(default_factory=set)
    linked_asset: set[str] = field(default_factory=set)
    unlinked_asset: set[str] = field(default_factory=set)
    ns_part_to_namelvl_list: dict[str, list[tuple[str, int]]] = field(default_factory=_defdict_list)
    ns_tree: _NsTree = field(default_factory=dict)

    def collect_postwrite_data(self, n: LogseqNode) -> None:
        """Collect data for post-write processing."""
        self.names.add(n.name)
        if n.is_ns:
            cur = self.ns_tree
            for level, part in enumerate(n.name.split("/"), start=1):
                self.ns_part_to_namelvl_list[part].append((n.name, level))
                cur = cur.setdefault(part, {})
        else:
            self.non_ns_names.add(n.name)

        if n.filetype == FileType.ASSET:
            if n.backlinked:
                self.linked_asset.add(n.name)
            else:
                self.unlinked_asset.add(n.name)


@dataclass(slots=True)
class LogseqNamespaceConflicts:
    """Class for analyzing namespace data in Logseq."""

    part_to_dangling: dict[str, set[str]] = field(default_factory=_defdict_set)
    part_to_nonnamespace: dict[str, set[str]] = field(default_factory=_defdict_set)
    part_to_lvl_to_parentname: dict = field(default_factory=lambda: defaultdict(_defdict_set))
    part_to_lvl_to_fullname: dict = field(default_factory=lambda: defaultdict(_defdict_set))

    def process_ns_conflicts(
        self, part_to_namelvl: dict[str, list[tuple[str, int]]], non_ns_name: set[str], dangling: set[str]
    ) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        for part, namelvl_list in part_to_namelvl.items():
            names = {n for n, _ in namelvl_list}
            if part in non_ns_name:
                self.part_to_nonnamespace[part].update(names)
            if part in dangling:
                self.part_to_dangling[part].update(names)
            if len(namelvl_list) <= 1:
                continue
            if len({lv for _, lv in namelvl_list}) <= 1:
                continue
            for name, lvl in namelvl_list:
                self.part_to_lvl_to_parentname[part][lvl].add("/".join(name.split("/")[:lvl]))
                self.part_to_lvl_to_fullname[part][lvl].add(name)


@dataclass(slots=True)
class LogseqSummarizer:
    """Summarize Logseq analysis."""

    filetype: defaultdict[str, list[str]] = field(default_factory=_defdict_list)
    nodetype: defaultdict[str, list[str]] = field(default_factory=_defdict_list)
    extension: defaultdict[str, list[str]] = field(default_factory=_defdict_list)
    content: dict[str, dict] = field(default_factory=dict)

    def summarize(self, n: LogseqNode) -> None:
        """Post process a file for summarization. Depends on certain properties being set in the file."""
        self.extension[n.path.suffix].append(n.name)
        self.filetype[n.filetype].append(n.name)
        self.nodetype[n.nodetype].append(n.name)
        for k, v in n.data.items():
            data_item = self.content.setdefault(k, {})
            _update_counts(data_item, v, n.name)


@dataclass(slots=True)
class LogseqAnalyzer:
    """Class for post-processing Logseq graph data after initial analysis."""

    index: set[LogseqNode]
    jrnlfmt_page: str
    inputs: AnalysisInput = field(default_factory=AnalysisInput)
    prewrite: PreWrite = field(default_factory=PreWrite)
    postwrite: PostWrite = field(default_factory=PostWrite)
    namespace: LogseqNamespaceConflicts = field(default_factory=LogseqNamespaceConflicts)
    asset: defaultdict[str, set[str]] = field(default_factory=_defdict_set)
    journal: dict[str, list[datetime]] = field(default_factory=dict)
    dangling: set[str] = field(default_factory=set)
    summarizer: LogseqSummarizer = field(default_factory=LogseqSummarizer)

    def __call__(self) -> None:
        """Process the Logseq graph data for namespaces, linked references, and assets."""
        for n in self.index:
            self.inputs.collect_input_data(n)

        _linkedref_ns = self.inputs.linkedref_ns.difference(self.inputs.linkedref)
        for n in self.index:
            self.prewrite.collect_prewrite_data(n, self.inputs.linkedref, _linkedref_ns, self.inputs.to_mark_ns)

        for n in get_asset_to_backlink(self.inputs.asset_to_link, self.inputs.asset_mention):
            # TODO: Refactor
            n.backlinked = True
        for n in self.prewrite.graph_to_link:
            # TODO: Refactor
            n.backlinked = True
        for n in self.prewrite.graph_to_link_ns:
            # TODO: Refactor
            n.backlinked_ns_only = True
        for n in self.prewrite.graph_to_ns:
            # TODO: Refactor
            n.is_ns = True
        for n in self.index:
            # TODO: Refactor
            n.nodetype = n.get_nodetype()

        linkedref = self.inputs.linkedref.difference({n.name for n in self.prewrite.graph_to_link})
        linkedref_ns = self.inputs.linkedref_ns.difference({n.name for n in self.prewrite.graph_to_link_ns})

        for n in self.index:
            self.postwrite.collect_postwrite_data(n)
            self.summarizer.summarize(n)

        self.dangling.update(get_dangling(linkedref | linkedref_ns, self.postwrite.names, self.inputs.aliases))
        self.namespace.process_ns_conflicts(
            self.postwrite.ns_part_to_namelvl_list, self.postwrite.non_ns_names, self.dangling
        )
        self.journal.update(process_journal(self.inputs.journal_names, self.dangling, self.jrnlfmt_page))
        self.asset["asset_backlinked"].update(self.postwrite.linked_asset)
        self.asset["asset_not_backlinked"].update(self.postwrite.unlinked_asset)
