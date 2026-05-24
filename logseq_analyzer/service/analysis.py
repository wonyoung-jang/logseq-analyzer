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


type _NsTree = dict[str, "_NsTree"]


def _update_counts(result: dict, collection: Iterable[str], filename: str) -> None:
    """Update the result dictionary with counts and file occurrences."""
    for item in collection:
        entry = result.setdefault(item, {"count": 0, "found_in": Counter()})
        entry["count"] += 1
        entry["found_in"][filename] += 1


def _journal_to_dt(keys: Iterable[str], jrnlfmt_page: str) -> Iterator[datetime]:
    """Convert journal keys from strings to datetime objects."""
    for key in keys:
        k = DT_ORDINAL_PATTERN.sub("", key)
        try:
            yield datetime.strptime(k, jrnlfmt_page).replace(tzinfo=UTC)
        except ValueError:
            continue


@dataclass(slots=True)
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    aliases: set[str] = field(default_factory=set)
    dangling: set[str] = field(default_factory=set)
    linkedref_count: dict = field(default_factory=dict)
    linkedref: set[str] = field(default_factory=set)
    linkedref_ns: set[str] = field(default_factory=set)
    to_mark_ns: set[str] = field(default_factory=set)

    def process_graph(self, f: LogseqNode) -> None:
        """Process a file to find linked references and aliases."""
        self.aliases.update(f.get_data(Crit.Content.ALIAS))
        linkedrefs = set(chain.from_iterable(f.get_data(key) for key in LINKEDREF_CRITERIA))
        self.linkedref.update(linkedrefs)
        _update_counts(self.linkedref_count, linkedrefs, f.name)
        if f.is_ns:
            _update_counts(self.linkedref_count, {f.ns_root, f.ns_parent}, f.name)
            self.linkedref_ns.update({f.name, f.ns_root, f.ns_parent})
            self.to_mark_ns.add(f.ns_root)

    def process_node(self, f: LogseqNode) -> str:
        """Process summary data for a single file based on metadata and content analysis."""
        if f.name in self.linkedref:
            self.linkedref.remove(f.name)
            return "backlinked"
        if f.name in self.linkedref_ns:
            self.linkedref_ns.remove(f.name)
            return "backlinked_ns"
        return "none"

    def process_dangling(self, names: set[str]) -> None:
        """Get the set of dangling links from a given set of names."""
        self.dangling.update((self.linkedref | self.linkedref_ns) - names - self.aliases - LOGSEQ_BUILTIN_PROPERTY)


@dataclass(slots=True)
class LogseqAssets:
    """Analyze assets in Logseq."""

    backlinked: set[str] = field(default_factory=set)
    not_backlinked: set[str] = field(default_factory=set)
    hls_name: set[str] = field(default_factory=set)
    hls_bullet: set[str] = field(default_factory=set)
    hls_backlinked: set[str] = field(default_factory=set)
    hls_not_backlinked: set[str] = field(default_factory=set)
    asset_mention: set[str] = field(default_factory=set)

    def process(self, f: LogseqNode) -> None:
        """Process a file to find mentions of assets and determine if they are backlinked."""
        if f.filetype == FileType.SUB_ASSET:
            self.hls_name.add(f.name)
        if f.is_hls:
            self.hls_bullet.update(f.get_data(Crit.Content.HLS_BULLET))
        self.asset_mention.update(chain.from_iterable(f.get_data(key) for key in ASSETMENTION_CRITERIA))

    def get_asset_to_backlink(
        self, hls_asset: set[LogseqNode], unlinked_asset: set[LogseqNode]
    ) -> Iterator[LogseqNode]:
        """Get the assets that need to be backlinked based on the index."""
        yield from (f for f in hls_asset if f.name in self.hls_bullet)
        yield from (f for f in unlinked_asset if any(f.name in m for m in self.asset_mention))

    def update_asset_backlinks(self, linked_asset: set[str], unlinked_asset: set[str]) -> None:
        """Update the sets of backlinked and not backlinked assets based on the index."""
        self.hls_not_backlinked.update(self.hls_name - self.hls_bullet)
        self.hls_backlinked.update(self.hls_name & self.hls_bullet)
        self.backlinked.update(linked_asset)
        self.not_backlinked.update(unlinked_asset)


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    part_to_namelvl_list: defaultdict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
    conflict_dangling_part_to_name: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    conflict_nonnamespace_part_to_name: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    conflict_part_to_lvl_to_parentname: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    conflict_part_to_lvl_to_fullname: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    lvl_to_partlist: dict[int, list[str]] = field(default_factory=lambda: defaultdict(list))
    tree: _NsTree = field(default_factory=dict)

    def process(self, f: LogseqNode) -> None:
        """Initialize namespace parts for a given file."""
        if f.is_ns:
            cur = self.tree
            for level, part in enumerate(f.ns_part, start=1):
                self.part_to_namelvl_list[part].append((f.name, level))
                self.lvl_to_partlist[level].append(part)
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
class LogseqJournals:
    """LogseqJournals class to handle journal files and their processing."""

    data: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))

    def process(self, journals: set[str], dangling: set[str], jrnlfmt_page: str) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        self.data["existing"].extend(sorted(_journal_to_dt(journals, jrnlfmt_page)))
        self.data["dangling"].extend(sorted(_journal_to_dt(dangling, jrnlfmt_page)))
        dangling_set = set(self.data["dangling"])
        existing = self.data["existing"]
        n_existing = len(existing)
        for i, date in enumerate(existing, start=1):
            _expected = date + timedelta(days=1)
            while i < n_existing and _expected < existing[i]:
                if _expected not in dangling_set:
                    self.data["missing"].append(_expected)
                _expected = _expected + timedelta(days=1)


@dataclass(slots=True)
class LogseqSummarizer:
    """Summarize Logseq analysis."""

    file: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetype: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetype: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extension: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
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
    graph: LogseqGraph = field(default_factory=LogseqGraph)
    asset: LogseqAssets = field(default_factory=LogseqAssets)
    namespace: LogseqNamespaces = field(default_factory=LogseqNamespaces)
    journal: LogseqJournals = field(default_factory=LogseqJournals)
    summary: LogseqSummarizer = field(default_factory=LogseqSummarizer)

    def process(self) -> None:
        """Process the Logseq graph data for namespaces, linked references, and assets."""
        for f in self.index:
            self.graph.process_graph(f)
            self.asset.process(f)
        self.graph.linkedref_ns.difference_update(self.graph.linkedref)
        self._processnode()
        self._postprocess()
        self._summarize()

    def _processnode(self) -> None:
        """Process node data."""
        d = defaultdict(set)
        for f in self.index:
            if f.name in self.graph.to_mark_ns and not f.is_ns:
                f.is_ns = True  # TODO: Refactor
            self.namespace.process(f)
            match self.graph.process_node(f):
                case "backlinked":
                    f.backlinked = True  # TODO: Refactor
                case "backlinked_ns":
                    f.backlinked_ns_only = True  # TODO: Refactor
            if f.filetype == FileType.SUB_ASSET:
                d["hls_asset"].add(f)
            if f.filetype == FileType.ASSET and not f.backlinked:
                d["unlinked_asset"].add(f)
        for f in self.asset.get_asset_to_backlink(
            hls_asset=d["hls_asset"],
            unlinked_asset=d["unlinked_asset"],
        ):
            f.backlinked = True  # TODO: Refactor

    def _postprocess(self) -> None:
        """Post process the Logseq graph data for summarization."""
        d = defaultdict(set)
        for f in self.index:
            d["names"].add(f.name)
            if not f.is_ns:
                d["non_ns_names"].add(f.name)
            if f.filetype == FileType.JOURNAL:
                d["journal_names"].add(f.name)
            if f.filetype == FileType.ASSET:
                if f.backlinked:
                    d["linked_asset"].add(f.name)
                else:
                    d["unlinked_asset"].add(f.name)
        self.graph.process_dangling(d["names"])
        self.namespace.process_conflicts(
            non_ns_names=d["non_ns_names"],
            dangling=self.graph.dangling,
        )
        self.journal.process(
            journals=d["journal_names"],
            dangling=self.graph.dangling,
            jrnlfmt_page=self.jrnlfmt_page,
        )
        self.asset.update_asset_backlinks(
            linked_asset=d["linked_asset"],
            unlinked_asset=d["unlinked_asset"],
        )

    def _summarize(self) -> None:
        """Summarize the Logseq graph data."""
        for f in self.index:
            self.summary.process(f)
