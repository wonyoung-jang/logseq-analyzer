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

from logseq_analyzer.domain.enums import ASSETMENTION_CRITERIA, LINKEDREF_CRITERIA, Crit, FileType, Output
from logseq_analyzer.domain.model import LOGSEQ_BUILTIN_PROPERTY, LogseqNode
from logseq_analyzer.domain.patterns import DT_ORDINAL_PATTERN

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


logger = logging.getLogger(__name__)


type _NsTree = dict[str, _NsTree]


def _update_counts(result: dict, collection: Iterable[str], filename: str) -> None:
    """Update the result dictionary with counts and file occurrences."""
    for item in collection:
        entry = result.setdefault(item, {"count": 0, "found_in": Counter()})
        entry["count"] += 1
        entry["found_in"][filename] += 1


def get_dangling(linkedrefs: set[str], names: set[str], aliases: set[str]) -> set[str]:
    """Get the set of dangling links from a given set of names."""
    return linkedrefs - names - aliases - LOGSEQ_BUILTIN_PROPERTY


def _journal_to_dt(keys: Iterable[str], jrnlfmt_page: str) -> Iterator[datetime]:
    """Convert journal keys from strings to datetime objects."""
    for key in keys:
        k = DT_ORDINAL_PATTERN.sub("", key)
        try:
            yield datetime.strptime(k, jrnlfmt_page).replace(tzinfo=UTC)
        except ValueError:
            continue


def process_journal(journals: set[str], dangling: set[str], jrnlfmt_page: str) -> dict[str, list[datetime]]:
    """Build a complete timeline of journal entries, filling in any missing dates."""
    d = defaultdict(list)
    d["existing"].extend(sorted(_journal_to_dt(journals, jrnlfmt_page)))
    d["dangling"].extend(sorted(_journal_to_dt(dangling, jrnlfmt_page)))
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


def get_asset_to_backlink(
    hls_asset: set[LogseqNode], unlinked_asset: set[LogseqNode], hls_bullet: set[str], asset_mention: set[str]
) -> Iterator[LogseqNode]:
    """Get the assets that need to be backlinked based on the index."""
    yield from (n for n in hls_asset if n.name in hls_bullet)
    yield from (n for n in unlinked_asset if any(n.name in m for m in asset_mention))


@dataclass(slots=True)
class LogseqAnalysisInput:
    """Class to represent the input for Logseq analysis."""

    aliases: set[str] = field(default_factory=set)
    linkedref: set[str] = field(default_factory=set)
    linkedref_ns: set[str] = field(default_factory=set)
    to_mark_ns: set[str] = field(default_factory=set)
    hls_name: set[str] = field(default_factory=set)
    hls_bullet: set[str] = field(default_factory=set)
    asset_mention: set[str] = field(default_factory=set)

    def collect(self, n: LogseqNode) -> None:
        """Process a file to find linked references and aliases."""
        self.aliases.update(n.get_data(Crit.Content.ALIAS))
        self.linkedref.update(chain.from_iterable(n.get_data(key) for key in LINKEDREF_CRITERIA))
        self.asset_mention.update(chain.from_iterable(n.get_data(key) for key in ASSETMENTION_CRITERIA))
        if n.has_ns:
            self.to_mark_ns.add(n.ns_root)
            self.linkedref_ns.update({n.name, n.ns_root, n.ns_parent})
        if n.filetype == FileType.SUB_ASSET:
            self.hls_name.add(n.name)
        if n.is_hls:
            self.hls_bullet.update(n.get_data(Crit.Content.HLS_BULLET))


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    part_to_namelvl_list: dict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
    conflict_dangling_part_to_name: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    conflict_nonnamespace_part_to_name: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    conflict_part_to_lvl_to_parentname: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    conflict_part_to_lvl_to_fullname: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    tree: _NsTree = field(default_factory=dict)

    def process(self, ns_nodes: set[LogseqNode]) -> None:
        """Initialize namespace parts for a given file."""
        for n in ns_nodes:
            cur = self.tree
            for level, part in enumerate(n.ns_part, start=1):
                self.part_to_namelvl_list[part].append((n.name, level))
                cur = cur.setdefault(part, {})

    def process_conflicts(self, non_ns_names: set[str], dangling: set[str]) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        in_non_ns = self.part_to_namelvl_list.keys() & non_ns_names
        in_dangling = self.part_to_namelvl_list.keys() & dangling
        for part, name_lvl_list in self.part_to_namelvl_list.items():
            names = {name for name, _ in name_lvl_list}
            if part in in_non_ns:
                self.conflict_nonnamespace_part_to_name[part].update(names)
            if part in in_dangling:
                self.conflict_dangling_part_to_name[part].update(names)
            if len(name_lvl_list) <= 1 or len({lvl for _, lvl in name_lvl_list}) <= 1:
                continue
            for name, lvl in name_lvl_list:
                self.conflict_part_to_lvl_to_parentname[part][lvl].add("/".join(name.split("/")[:lvl]))
                self.conflict_part_to_lvl_to_fullname[part][lvl].add(name)


@dataclass(slots=True)
class LogseqSummarizer:
    """Summarize Logseq analysis."""

    file: defaultdict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetype: defaultdict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetype: defaultdict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extension: defaultdict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    content: dict[str, dict] = field(default_factory=dict)

    def process(self, f: LogseqNode) -> None:
        """Post process a file for summarization. Depends on certain properties being set in the file."""
        self.filetype[f.filetype].append(f.name)
        self.extension[f.path.suffix].append(f.name)
        self.nodetype[f.nodetype].append(f.name)
        for k, v in {
            Output.File.SUMMARY_HAS_CONTENT: f.has_content,
            Output.File.SUMMARY_HAS_BACKLINK: f.has_backlinks,
            Output.File.SUMMARY_BACKLINKED: f.backlinked,
            Output.File.SUMMARY_BACKLINKED_NS_ONLY: f.backlinked_ns_only,
            Output.File.SUMMARY_IS_HLS: f.is_hls,
        }.items():
            if v:
                self.file[k].append(f.name)
        for k, v in f.data.items():
            data_item = self.content.setdefault(k, {})
            _update_counts(data_item, v, f.name)


@dataclass(slots=True)
class LogseqAnalyzer:
    """Class for post-processing Logseq graph data after initial analysis."""

    index: set[LogseqNode]
    jrnlfmt_page: str
    inputs: LogseqAnalysisInput = field(default_factory=LogseqAnalysisInput)
    namespace: LogseqNamespaces = field(default_factory=LogseqNamespaces)
    summary: LogseqSummarizer = field(default_factory=LogseqSummarizer)
    asset: defaultdict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    journal: dict[str, list[datetime]] = field(default_factory=dict)
    dangling: set[str] = field(default_factory=set)

    def process(self) -> None:
        """Process the Logseq graph data for namespaces, linked references, and assets."""
        for n in self.index:
            self.inputs.collect(n)

        self.inputs.linkedref_ns.difference_update(self.inputs.linkedref)
        graph_to_link = {n for n in self.index if n.name in self.inputs.linkedref}
        graph_to_link_ns = {n for n in self.index if n.name in self.inputs.linkedref_ns}
        self.inputs.linkedref.difference_update({n.name for n in graph_to_link})
        self.inputs.linkedref_ns.difference_update({n.name for n in graph_to_link_ns})
        graph_to_ns = {n for n in self.index if n.name in self.inputs.to_mark_ns and not n.is_ns}
        hls_asset_to_link = {n for n in self.index if n.filetype == FileType.SUB_ASSET}
        unlinked_asset_to_link = {n for n in self.index if n.filetype == FileType.ASSET and not n.backlinked}
        for n in graph_to_link:
            n.backlinked = True  # TODO: Refactor
        for n in graph_to_link_ns:
            n.backlinked_ns_only = True  # TODO: Refactor
        for n in graph_to_ns:
            n.is_ns = True  # TODO: Refactor
        for n in get_asset_to_backlink(
            hls_asset_to_link, unlinked_asset_to_link, self.inputs.hls_bullet, self.inputs.asset_mention
        ):
            n.backlinked = True  # TODO: Refactor

        namespace_nodes = {n for n in self.index if n.is_ns}
        self.namespace.process(namespace_nodes)

        names = {n.name for n in self.index}
        non_ns_names = {n.name for n in self.index if not n.is_ns}
        journal_names = {n.name for n in self.index if n.filetype == FileType.JOURNAL}
        linked_asset = {n.name for n in self.index if n.filetype == FileType.ASSET and n.backlinked}
        unlinked_asset = {n.name for n in self.index if n.filetype == FileType.ASSET and not n.backlinked}
        self.dangling.update(get_dangling(self.inputs.linkedref | self.inputs.linkedref_ns, names, self.inputs.aliases))
        self.namespace.process_conflicts(non_ns_names, self.dangling)
        self.journal.update(process_journal(journal_names, self.dangling, self.jrnlfmt_page))
        self.asset["asset_backlinked"].update(linked_asset)
        self.asset["asset_not_backlinked"].update(unlinked_asset)
        self.asset["hls_asset_not_backlinked"].update(self.inputs.hls_name - self.inputs.hls_bullet)
        self.asset["hls_asset_backlinked"].update(self.inputs.hls_name & self.inputs.hls_bullet)
        for n in self.index:
            self.summary.process(n)
