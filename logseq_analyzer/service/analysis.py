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

from logseq_analyzer.domain.model import BUILT_IN_PROPERTIES
from logseq_analyzer.utils.enums import Core, Crit, FileType, Output
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from logseq_analyzer.domain.model import FileIndex, LogseqFile

logger = logging.getLogger(__name__)

_DATE_ORDINAL_SUFFIXES: frozenset[str] = frozenset(("st", "nd", "rd", "th"))

type _NsTree = dict[str, "_NsTree"]


class _QueryInfo(TypedDict, total=False):
    found_in: list[str]
    namespace: str
    size: int


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
    """Update the result dictionary with counts and file occurrences.

    Args:
        result (dict): The dictionary to update with counts and file occurrences.
        collection (Iterable[str]): The collection of items to count.
        filename (str): The name of the file containing the path information.

    """
    for item in collection:
        entry = result.setdefault(item, {"count": 0, "found_in": Counter()})
        entry["count"] += 1
        entry["found_in"][filename] += 1


def _process_namespaces(f: LogseqFile, from_name: Callable[[str], list[LogseqFile]]) -> None:
    """Post-process namespaces in the content data."""
    for root in from_name(f.ns_info.root):
        root.ns_info.mark_as_namespace_root()  # TODO: Refactor
        root.ns_info.add_child(f.name)  # TODO: Refactor
    for parent in from_name(f.ns_info.parent_full):
        parent.ns_info.add_child(f.name)  # TODO: Refactor


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

    dangling: set[str] = field(default_factory=set)
    dangling_count: dict = field(default_factory=dict)
    linkedref: set[str] = field(default_factory=set)
    linkedref_ns: set[str] = field(default_factory=set)
    linkedref_count: dict = field(default_factory=dict)
    aliases: set[str] = field(default_factory=set)

    def process_graph(self, f: LogseqFile, from_name: Callable[[str], list[LogseqFile]]) -> None:
        """Process a file to find linked references and aliases."""
        if f.ns_info.is_namespace:
            self.linkedref_ns.add(f.name)
            self.linkedref_ns.add(f.ns_info.root)
            _process_namespaces(f, from_name)
        self.aliases.update(f.get_data(Crit.Content.ALIASES))
        self.linkedref.update(f.yield_linkedrefs())
        _update_counts(self.linkedref_count, f.yield_linkedrefs(), f.name)
        if f.ns_info.parent_full:
            _update_counts(self.linkedref_count, [f.ns_info.parent_full], f.name)

    def process_node(self, f: LogseqFile) -> None:
        """Process summary data for a single file based on metadata and content analysis."""
        if f.name in self.linkedref:
            self.linkedref.remove(f.name)
            f.node.mark_backlinked()  # TODO: Refactor
        elif f.name in self.linkedref_ns:
            self.linkedref_ns.remove(f.name)
            f.node.mark_backlinked_ns_only()  # TODO: Refactor
        f.set_nodetype()  # TODO: Refactor

    def process_dangling(self, names: set[str]) -> None:
        """Get the set of dangling links from a given set of names."""
        self.dangling.update((self.linkedref | self.linkedref_ns) - names - self.aliases - BUILT_IN_PROPERTIES)
        self.dangling_count.update({k: v for k, v in self.linkedref_count.items() if k in self.dangling})

    @property
    def report(self) -> dict:
        """Generate a report of the graph analysis."""
        return {Output.Dir.GRAPH: {k: getattr(self, k) for k in self.__slots__}}


@dataclass(slots=True)
class LogseqAssets:
    """Analyze assets in Logseq."""

    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)
    hls_asset_map: dict[str, LogseqFile] = field(default_factory=dict)
    hls_bullets: set[str] = field(default_factory=set)
    hls_backlinked: set[str] = field(default_factory=set)
    hls_not_backlinked: set[str] = field(default_factory=set)
    asset_mentions: set[str] = field(default_factory=set)

    def process(self, f: LogseqFile) -> None:
        """Process a file to find mentions of assets and determine if they are backlinked."""
        if f.filetype == FileType.SUB_ASSET:
            self.hls_asset_map[f.name] = f
        if f.is_hls:
            self.hls_bullets.update(f.yield_hls_bullet())
        self.asset_mentions.update(f.yield_asset_mentions())

    def process_hls_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        if not self.hls_asset_map:
            return
        for name in self.hls_bullets:
            if not (hls_file := self.hls_asset_map.get(name)):
                self.hls_not_backlinked.add(name)
                continue
            hls_file.set_filetype(FileType.ASSET)  # TODO: Refactor
            hls_file.node.mark_backlinked()  # TODO: Refactor
            self.hls_backlinked.add(name)

    def process_asset_backlinks(self, index: FileIndex) -> None:
        """Process a file to find mentions of assets and determine if they are backlinked."""
        if not self.asset_mentions:
            return
        for unlinked in index.yield_backlinked_assets(backlinked=False):
            if any(unlinked.name in m for m in self.asset_mentions):
                unlinked.node.mark_backlinked()  # TODO: Refactor
        self.backlinked.update(index.yield_backlinked_assets(backlinked=True))
        self.not_backlinked.update(index.yield_backlinked_assets(backlinked=False))

    @property
    def report(self) -> dict:
        """Generate a report of the asset analysis."""
        return {Output.Dir.ASSETS: {k: getattr(self, k) for k in self.__slots__}}


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
    queries: dict[str, _QueryInfo] = field(default_factory=dict)

    def process(self, f: LogseqFile) -> None:
        """Initialize namespace parts for a given file."""
        if not f.ns_info.is_namespace or not (parts := f.ns_info.parts):
            return
        cur = self.tree
        for part, level in parts:
            self.part_to_namelvl_list[part].append((f.name, level))
            self.lvl_to_partlist[level].append(part)
            cur = cur.setdefault(part, {})
        for query in f.get_data(Crit.DblCurly.NAMESPACE_QUERY):
            page_refs = ContentPatterns.PAGE_REFERENCE.findall(query)
            if len(page_refs) != 1:
                logger.warning("Invalid query: %s", query)
                continue
            if query not in self.queries:
                self.queries[query] = {
                    "found_in": [f.name],
                    "namespace": page_refs[0],
                    "size": f.ns_info.size,
                }
            else:
                self.queries[query]["found_in"].append(f.name)

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

    @property
    def report(self) -> dict:
        """Generate a report of the namespace analysis."""
        return {Output.Dir.NAMESPACES: {k: getattr(self, k) for k in self.__slots__}}


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

    @property
    def report(self) -> dict[str, dict[str, object]]:
        """Get a report of the journal processing results."""
        return {Output.Dir.JOURNALS: {k: getattr(self, k) for k in self.__slots__}}


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
        """Process a file for summarization."""
        self.extension[f.path.suffix].append(f.name)
        if f.is_hls:
            self.file[Output.File.SUMMARY_IS_HLS].append(f.name)
        if f.node.has_content:
            self.file[Output.File.SUMMARY_HAS_CONTENT].append(f.name)
        if f.node.has_backlinks:
            self.file[Output.File.SUMMARY_HAS_BACKLINKS].append(f.name)
        for k, v in f.data.items():
            data_item = self.content.setdefault(k, {})
            _update_counts(data_item, v, f.name)

    def process_node(self, f: LogseqFile) -> None:
        """Post process a file for summarization. Depends on certain properties being set in the file."""
        self.filetype[f.filetype].append(f.name)
        self.nodetype[f.node.nodetype].append(f.name)
        if f.node.backlinked:
            self.file[Output.File.SUMMARY_BACKLINKED].append(f.name)
        if f.node.backlinked_ns_only:
            self.file[Output.File.SUMMARY_BACKLINKED_NS_ONLY].append(f.name)
        self.info[f.name] = {}
        self.info[f.name]["file"] = f.file_info
        self.info[f.name]["namespace"] = f.ns_info

    @property
    def report(self) -> dict:
        """Generate a report of the summarization."""
        return {
            Output.Dir.SUMMARY: {
                Output.File.SUMMARY_FILE_FILETYPE: self.filetype,
                Output.File.SUMMARY_FILE_NODETYPE: self.nodetype,
                Output.File.SUMMARY_FILE_EXTENSION: self.extension,
                Output.File.SUMMARY_CONTENT_INFO: self.info,
            },
            Output.Dir.SUMMARY_FILE_GENERAL: self.file,
            Output.Dir.SUMMARY_CONTENT: self.content,
        }


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
            self.graph.process_graph(f, self.index.get_from_name)
            self.asset.process(f)
            self.namespace.process(f)
            self.summary.process(f)
        # 2. Second pass (requires pass 1)
        for f in self.index:
            self.graph.process_node(f)
        # 3. Post processing
        self.graph.process_dangling(set(self.index.yield_names()))
        self.asset.process_hls_backlinks()
        self.asset.process_asset_backlinks(self.index)
        self.namespace.process_conflicts(self.index.yield_non_ns_names(), self.graph.dangling)
        self.journal.process(self.index.yield_journals(), self.graph.dangling, self.journal_page_fmt)
        # 4. Third pass (requires step 1, 2, and 3)
        for f in self.index:
            self.summary.process_node(f)
