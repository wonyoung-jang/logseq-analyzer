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
from typing import TYPE_CHECKING, TypedDict

from logseq_analyzer.domain.enums import Core, Crit, FileType, Output
from logseq_analyzer.domain.model import BUILT_IN_PROPERTIES

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from logseq_analyzer.domain.model import FileIndex, LogseqFile

logger = logging.getLogger(__name__)

_DATE_ORDINAL_SUFFIXES: frozenset[str] = frozenset(("st", "nd", "rd", "th"))

type _NsTree = dict[str, "_NsTree"]


class JournalStat(TypedDict):
    """TypedDict for journal statistics."""

    first: datetime
    last: datetime
    days: int


def _get_journal_stats(dates: list[datetime]) -> JournalStat:
    """Get statistics about the timeline."""
    first = min(dates) if dates else datetime.min.replace(tzinfo=UTC)
    last = max(dates) if dates else datetime.min.replace(tzinfo=UTC)
    delta = last - first
    days = delta.days + 1
    return JournalStat(first=first, last=last, days=days)


def _update_counts(result: dict, collection: Iterable[str], filename: str) -> None:
    """Update the result dictionary with counts and file occurrences."""
    for item in collection:
        entry = result.setdefault(item, {"count": 0, "found_in": Counter()})
        entry["count"] += 1
        entry["found_in"][filename] += 1


def _journals_to_datetime(keys: Iterable[str], journal_page_fmt: str) -> Iterator[datetime]:
    """Convert journal keys from strings to datetime objects."""
    fmt = journal_page_fmt.replace("#", "")
    for key in keys:
        k = key
        for ordinal in _DATE_ORDINAL_SUFFIXES:
            k = k.replace(ordinal, "")
        try:
            yield datetime.strptime(k, fmt).replace(tzinfo=UTC)
        except ValueError:
            logger.warning("Failed to parse journal key '%s' with format '%s'", key, fmt)


@dataclass(slots=True)
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    aliases: set[str] = field(default_factory=set)
    dangling: set[str] = field(default_factory=set)
    dangling_count: dict = field(default_factory=dict)
    linkedref_count: dict = field(default_factory=dict)
    linkedref: set[str] = field(default_factory=set)
    linkedref_ns: set[str] = field(default_factory=set)
    to_mark_ns: set[str] = field(default_factory=set)

    def process_graph(self, f: LogseqFile) -> None:
        """Process a file to find linked references and aliases."""
        self.aliases.update(f.get_data(Crit.Content.ALIAS))
        linkedrefs = set(f.yield_linkedrefs())
        self.linkedref.update(linkedrefs)
        _update_counts(self.linkedref_count, linkedrefs, f.name)
        if f.ns_info.is_namespace:
            _update_counts(self.linkedref_count, {f.ns_info.root, f.ns_info.parent}, f.name)
            self.linkedref_ns.update({f.name, f.ns_info.root, f.ns_info.parent})
            self.to_mark_ns.add(f.ns_info.root)

    def process_node(self, f: LogseqFile) -> str:
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
        self.dangling.update((self.linkedref | self.linkedref_ns) - names - self.aliases - BUILT_IN_PROPERTIES)
        self.dangling_count.update({k: v for k, v in self.linkedref_count.items() if k in self.dangling})


@dataclass(slots=True)
class LogseqAssets:
    """Analyze assets in Logseq."""

    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)
    hls_map: dict[str, LogseqFile] = field(default_factory=dict)
    hls_bullet: set[str] = field(default_factory=set)
    hls_backlinked: set[str] = field(default_factory=set)
    hls_not_backlinked: set[str] = field(default_factory=set)
    asset_mention: set[str] = field(default_factory=set)

    def process(self, f: LogseqFile) -> None:
        """Process a file to find mentions of assets and determine if they are backlinked."""
        if f.filetype == FileType.SUB_ASSET:
            self.hls_map[f.name] = f
        if f.is_hls:
            self.hls_bullet.update(f.yield_hls_bullet())
        self.asset_mention.update(f.yield_asset_mentions())

    def update_asset_backlinks(self, linked_asset: Iterable[LogseqFile], unlinked_asset: Iterable[LogseqFile]) -> None:
        """Update the sets of backlinked and not backlinked assets based on the index."""
        self.hls_not_backlinked.update(self.hls_map.keys() - self.hls_bullet)
        self.hls_backlinked.update(self.hls_map.keys() & self.hls_bullet)
        self.backlinked.update(linked_asset)
        self.not_backlinked.update(unlinked_asset)

    def get_asset_to_backlink(self, unlinked_asset: Iterator[LogseqFile]) -> Iterator[LogseqFile]:
        """Get the assets that need to be backlinked based on the index."""
        yield from (f for n, f in self.hls_map.items() if n in self.hls_bullet)
        yield from (f for f in unlinked_asset if any(f.name in m for m in self.asset_mention))


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    part_to_namelvl_list: defaultdict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
    conflict_dangling_part_to_name: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    conflict_nonnamespace_part_to_name: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    conflict_part_to_lvl_to_parentname: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    conflict_part_to_lvl_to_fullname: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    lvl_to_partlist: dict[int, list[str]] = field(default_factory=lambda: defaultdict(list))
    tree: _NsTree = field(default_factory=dict)

    def process(self, f: LogseqFile) -> None:
        """Initialize namespace parts for a given file."""
        if f.ns_info.is_namespace:
            cur = self.tree
            for level, part in enumerate(f.ns_info.part, start=1):
                self.part_to_namelvl_list[part].append((f.name, level))
                self.lvl_to_partlist[level].append(part)
                cur = cur.setdefault(part, {})

    def process_conflicts(self, non_ns_names: Iterable[str], dangling: set[str]) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        unique = set(self.part_to_namelvl_list)
        in_non_ns = unique.intersection(non_ns_names)
        in_dangling = unique.intersection(dangling)
        for part, name_lvl_list in self.part_to_namelvl_list.items():
            names = {name for name, _ in name_lvl_list}
            if part in in_non_ns:
                self.conflict_nonnamespace_part_to_name[part].extend(names)
            if part in in_dangling:
                self.conflict_dangling_part_to_name[part].extend(names)
            if len(name_lvl_list) <= 1 or len({lvl for _, lvl in name_lvl_list}) <= 1:
                continue
            for name, lvl in name_lvl_list:
                self.conflict_part_to_lvl_to_parentname[part][lvl].add(Core.NS_SEP.join(name.split(Core.NS_SEP)[:lvl]))
                self.conflict_part_to_lvl_to_fullname[part][lvl].add(name)


@dataclass(slots=True)
class LogseqJournals:
    """LogseqJournals class to handle journal files and their processing."""

    total: list[datetime] = field(default_factory=list)
    existing: list[datetime] = field(default_factory=list)
    existing_timeline: list[datetime] = field(default_factory=list)
    not_existing_or_referenced: list[datetime] = field(default_factory=list)
    dangling: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))
    stat: dict[str, JournalStat] = field(default_factory=dict)

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.existing_timeline)

    def process(self, journals: Iterable[str], dangling: set[str], journal_page_fmt: str) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        dangling_dt = sorted(_journals_to_datetime(dangling, journal_page_fmt))
        self.existing.extend(sorted(_journals_to_datetime(journals, journal_page_fmt)))
        for i, date in enumerate(self.existing):
            self.existing_timeline.append(date)
            _expected = date + timedelta(days=1)
            _existing = self.existing[i + 1] if i + 1 < len(self.existing) else None
            while _existing and _expected < _existing:
                self.existing_timeline.append(_expected)
                if _expected not in dangling_dt:
                    self.not_existing_or_referenced.append(_expected)
                else:
                    self.dangling["within_existing"].append(_expected)
                _expected = _expected + timedelta(days=1)
        self.total.extend(sorted(set(chain(self.existing_timeline, dangling_dt))))
        self.stat["existing"] = _get_journal_stats(self.existing)
        self.stat["dangling"] = _get_journal_stats(dangling_dt)
        self.stat["total"] = _get_journal_stats(self.total)
        self.dangling["before_existing"].extend(d for d in dangling_dt if d < self.stat["existing"]["first"])
        self.dangling["after_existing"].extend(d for d in dangling_dt if d > self.stat["existing"]["last"])


@dataclass(slots=True)
class LogseqSummarizer:
    """Summarize Logseq analysis."""

    file: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetype: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetype: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extension: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    content: dict[str, dict] = field(default_factory=dict)
    info: dict[str, dict] = field(default_factory=dict)

    def process(self, f: LogseqFile) -> None:
        """Post process a file for summarization. Depends on certain properties being set in the file."""
        self.filetype[f.filetype].append(f.name)
        self.extension[f.path.suffix].append(f.name)
        self.nodetype[f.node.nodetype].append(f.name)
        if f.node.backlinked:
            self.file[Output.File.SUMMARY_BACKLINKED].append(f.name)
        if f.node.backlinked_ns_only:
            self.file[Output.File.SUMMARY_BACKLINKED_NS_ONLY].append(f.name)
        if f.ns_info.is_namespace:
            self.info[f.name] = {"namespace": f.ns_info}
        if f.is_hls:
            self.file[Output.File.SUMMARY_IS_HLS].append(f.name)
        if f.node.has_content:
            self.file[Output.File.SUMMARY_HAS_CONTENT].append(f.name)
        if f.node.has_backlinks:
            self.file[Output.File.SUMMARY_HAS_BACKLINK].append(f.name)
        for k, v in f.data.items():
            data_item = self.content.setdefault(k, {})
            _update_counts(data_item, v, f.name)


@dataclass(slots=True)
class LogseqAnalyzer:
    """Class for post-processing Logseq graph data after initial analysis."""

    index: FileIndex
    journal_page_fmt: str
    graph: LogseqGraph = field(default_factory=LogseqGraph)
    asset: LogseqAssets = field(default_factory=LogseqAssets)
    namespace: LogseqNamespaces = field(default_factory=LogseqNamespaces)
    journal: LogseqJournals = field(default_factory=LogseqJournals)
    summary: LogseqSummarizer = field(default_factory=LogseqSummarizer)

    def process(self) -> None:
        """Process the Logseq graph data for namespaces, linked references, and assets."""
        # 1. First pass to gather data
        for f in self.index:
            self.graph.process_graph(f)
            self.asset.process(f)
        self.graph.linkedref_ns.difference_update(self.graph.linkedref)
        for f in self.index:
            if f.name in self.graph.to_mark_ns and not f.ns_info.is_namespace:
                f.ns_info.mark_as_namespace()  # TODO: Refactor
            self.namespace.process(f)
        self._processnode()
        self._postprocess()
        self._summarize()

    def _processnode(self) -> None:
        """Process node data."""
        for f in self.index:
            action = self.graph.process_node(f)
            match action:
                case "backlinked":
                    f.node.mark_backlinked()  # TODO: Refactor
                case "backlinked_ns":
                    f.node.mark_backlinked_ns()  # TODO: Refactor
            if f.filetype in (FileType.JOURNAL, FileType.PAGE):
                f.node.determine()  # TODO: Refactor
        for f in self.asset.get_asset_to_backlink(self.index.yield_backlinked_assets(backlinked=False)):
            f.node.mark_backlinked()  # TODO: Refactor

    def _postprocess(self) -> None:
        """Post process the Logseq graph data for summarization."""
        self.asset.update_asset_backlinks(
            self.index.yield_backlinked_assets(backlinked=True),
            self.index.yield_backlinked_assets(backlinked=False),
        )
        self.graph.process_dangling({f.name for f in self.index})
        self.namespace.process_conflicts(
            (f.name for f in self.index if not f.ns_info.is_namespace), self.graph.dangling
        )
        self.journal.process(
            (f.name for f in self.index if f.filetype == FileType.JOURNAL), self.graph.dangling, self.journal_page_fmt
        )

    def _summarize(self) -> None:
        """Summarize the Logseq graph data."""
        for f in self.index:
            self.summary.process(f)
