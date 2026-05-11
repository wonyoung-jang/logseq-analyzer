"""Module with functions for processing and analyzing Logseq graph data."""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum
from itertools import chain
from typing import TYPE_CHECKING, TypedDict

from logseq_analyzer.utils.enums import Core, Crit, FileType, Output, OutputDir
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES, get_count_and_foundin_data, sort_dict_by_value
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from logseq_analyzer.domain.file import LogseqFile
    from logseq_analyzer.domain.index import FileIndex

logger = logging.getLogger(__name__)
_TO_NODE_TYPE = frozenset((FileType.JOURNAL, FileType.PAGE))


@dataclass(slots=True)
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    index: FileIndex
    all_linked_refs: dict = field(default_factory=dict)
    all_dangling_links: dict = field(default_factory=dict)
    dangling_links: set[str] = field(default_factory=set)
    linked_refs: set[str] = field(default_factory=set)
    linked_refs_ns: set[str] = field(default_factory=set)
    aliases: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        for f in self.index:
            self._process_content(f)
        for f in self.index:
            self._process_nodes(f)
        self.sort_all_linked_references()
        self.process_dangling()

    def _process_content(self, f: LogseqFile) -> None:
        if f.info.namespace.is_namespace:
            self._process_namespaces(f)
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

    def _process_namespaces(self, f: LogseqFile) -> None:
        """Post-process namespaces in the content data."""
        self.linked_refs_ns.update((f.info.namespace.root, f.path.name))
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


"""Module containing functions for processing and analyzing namespace data in Logseq.

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


type _NsSlotData = dict[str, object]
type _NsTree = dict[str, "_NsTree"]


class _PartEntry(TypedDict):
    entry: str
    level: int


class _QueryInfo(TypedDict, total=False):
    found_in: list[str]
    namespace: str
    size: int
    uri: str
    logseq_url: str


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    index: FileIndex
    dangling_links: set[str]
    _part_levels: defaultdict[str, set[int]] = field(default_factory=lambda: defaultdict(set))
    _part_entries: defaultdict[str, list[_PartEntry]] = field(default_factory=lambda: defaultdict(list))
    conflicts_dangling: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    conflicts_non_namespace: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    conflicts_parent_depth: dict[tuple[str, int], list[str]] = field(default_factory=lambda: defaultdict(list))
    conflicts_parent_unique: dict[tuple[str, int], set[str]] = field(default_factory=lambda: defaultdict(set))
    data: dict[str, _NsSlotData] = field(default_factory=dict)
    details: dict[str, Counter[int]] = field(default_factory=dict)
    parts: dict[str, dict[str, int]] = field(default_factory=dict)
    tree: _NsTree = field(default_factory=dict)
    unique_ns_per_level: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_parts: set[str] = field(default_factory=set)
    queries: dict[str, _QueryInfo] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqNamespaces instance."""
        self.details["level_distribution"] = Counter()
        for f in self.index:
            self._init_ns_parts(f)
        for f in self.index:
            self._analyze_ns_queries(f)
        self.queries = sort_dict_by_value(self.queries, value="size", reverse=True)
        self.analyze_ns_conflicts()

    def _init_ns_parts(self, f: LogseqFile) -> None:
        """Initialize namespace parts for a given file."""
        if not f.info.namespace.is_namespace:
            return
        self.data[f.path.name] = f.info.namespace.as_dict
        if not (parts := f.info.namespace.parts):
            return
        self.parts[f.path.name] = parts
        cur = self.tree
        for part, level in parts.items():
            self.unique_parts.add(part)
            self.unique_ns_per_level[level].add(part)
            self.details["level_distribution"][level] += 1
            cur = cur.setdefault(part, {})
            self._part_levels[part].add(level)
            self._part_entries[part].append({"entry": f.path.name, "level": level})

    def _analyze_ns_queries(self, f: LogseqFile) -> None:
        if not (f_data := f.data):
            return
        if not (queries := f_data.get(Crit.DblCurly.NAMESPACE_QUERY)):
            return
        for query in queries:
            page_refs: list[str] = ContentPatterns.PAGE_REFERENCE.findall(query)
            if len(page_refs) != 1:
                logger.warning("Invalid query: %s", query)
                continue
            qinfo = self.queries.setdefault(query, {})
            qinfo.setdefault("found_in", []).append(f.path.name)
            qinfo["namespace"] = page_refs[0]
            qinfo["size"] = (
                _s if (_d := self.data.get(page_refs[0])) and (_s := _d.get("size")) and isinstance(_s, int) else 0
            )
            qinfo["uri"] = f.path.uri
            qinfo["logseq_url"] = f.path.logseq_url

    def analyze_ns_conflicts(self) -> None:
        """Check for conflicts between split namespace parts and existing non-namespace page names."""
        potential_non_ns = self.unique_parts.intersection(self.index.yield_non_ns_names())
        potential_dangling = self.unique_parts.intersection(self.dangling_links)
        for entry, parts in self.parts.items():
            for part in potential_non_ns.intersection(parts):
                self.conflicts_non_namespace[part].append(entry)
            for part in potential_dangling.intersection(parts):
                self.conflicts_dangling[part].append(entry)
        for part, levels in self._part_levels.items():
            if len(levels) < 2:
                continue
            for level in levels:
                key = (part, level)
                entries = (d["entry"] for d in self._part_entries[part] if d["level"] == level)
                for entry in entries:
                    up_to_level = entry.split(Core.NS_SEP)[:level]
                    self.conflicts_parent_unique[key].add(Core.NS_SEP.join(up_to_level))
                    self.conflicts_parent_depth[key].append(entry)

    @property
    def report(self) -> dict[str, object]:
        """Generate a report of the namespace analysis."""
        return {
            OutputDir.NAMESPACES: {
                Output.NS_CONFLICTS_DANGLING: self.conflicts_dangling,
                Output.NS_CONFLICTS_NON_NAMESPACE: self.conflicts_non_namespace,
                Output.NS_CONFLICTS_PARENT_DEPTH: self.conflicts_parent_depth,
                Output.NS_CONFLICTS_PARENT_UNIQUE: self.conflicts_parent_unique,
                Output.NS_DATA: self.data,
                Output.NS_DETAILS: self.details,
                Output.NS_HIERARCHY: self.tree,
                Output.NS_PARTS: self.parts,
                Output.NS_UNIQUE_PARTS: self.unique_parts,
                Output.NS_UNIQUE_PER_LEVEL: self.unique_ns_per_level,
                Output.NS_QUERIES: self.queries,
            }
        }


"""Process logseq journals."""


class Day(IntEnum):
    """Enum for days of the week."""

    IN_WEEK = 7
    IN_MONTH = 30
    IN_YEAR = 365


_DATE_ORDINAL_SUFFIXES = frozenset(("st", "nd", "rd", "th"))


class JournalStat(TypedDict):
    """TypedDict for journal statistics."""

    first: datetime
    last: datetime
    days: int
    weeks: float
    months: float
    years: float


def _get_journal_stats(dates: list[datetime]) -> JournalStat:
    """Get statistics about the timeline."""
    first = min(dates) if dates else datetime.min.replace(tzinfo=UTC)
    last = max(dates) if dates else datetime.min.replace(tzinfo=UTC)
    delta = last - first
    days = delta.days + 1
    return JournalStat(
        first=first,
        last=last,
        days=days,
        weeks=round(days / Day.IN_WEEK, 2),
        months=round(days / Day.IN_MONTH, 2),
        years=round(days / Day.IN_YEAR, 2),
    )


@dataclass(slots=True)
class LogseqJournals:
    """LogseqJournals class to handle journal files and their processing."""

    index: FileIndex
    dangling_links: set[str]
    journal_page_format: str
    all_: list[datetime] = field(default_factory=list)
    existing: list[datetime] = field(default_factory=list)
    missing: list[datetime] = field(default_factory=list)
    timeline: list[datetime] = field(default_factory=list)
    dangling: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))
    stat: dict[str, JournalStat] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqJournals class."""
        _dangling_journals = sorted(self._journals_to_datetime(self.dangling_links))
        self.existing.extend(sorted(self._journals_to_datetime(self.index.yield_journals())))
        self.process(_dangling_journals)

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.timeline)

    def _journals_to_datetime(self, keys: Iterable[str]) -> Iterator[datetime]:
        """Convert journal keys from strings to datetime objects."""
        for key in keys:
            try:
                key_to_parse = key
                for ordinal in _DATE_ORDINAL_SUFFIXES:
                    key_to_parse = key_to_parse.replace(ordinal, "")
                yield datetime.strptime(key_to_parse, self.journal_page_format.replace("#", "")).replace(tzinfo=UTC)
            except ValueError:
                pass

    def process(self, dangling_dt: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        for i, date in enumerate(self.existing):
            self.timeline.append(date)
            _expected = date + timedelta(days=1)
            _existing = self.existing[i + 1] if i + 1 < len(self.existing) else None
            while _existing and _expected < _existing:
                self.timeline.append(_expected)
                if _expected not in dangling_dt:
                    self.missing.append(_expected)
                _expected = _expected + timedelta(days=1)
        self.all_.extend(sorted(chain(self.timeline, dangling_dt)))
        self.stat = {
            "timeline": _get_journal_stats(self.timeline),
            "dangling": _get_journal_stats(dangling_dt),
            "total": _get_journal_stats(self.all_),
        }
        for link in dangling_dt:
            if link < self.stat["timeline"]["first"]:
                self.dangling["past"].append(link)
            elif link > self.stat["timeline"]["last"]:
                self.dangling["future"].append(link)
            else:
                self.dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, object]:
        """Get a report of the journal processing results."""
        return {
            OutputDir.JOURNALS: {
                Output.JOURNALS_ALL: self.all_,
                Output.JOURNALS_DANGLING: self.dangling,
                Output.JOURNALS_EXISTING: self.existing,
                Output.JOURNALS_TIMELINE: self.timeline,
                Output.JOURNALS_MISSING: self.missing,
                Output.JOURNALS_TIMELINE_STATS: self.stat,
            }
        }


"""Logseq Assets Analysis Module."""


_ASSET_CRITERIA = frozenset((Crit.Emb.ASSET, Crit.Content.ASSETS))


@dataclass(slots=True)
class LogseqAssets:
    """Class to handle HLS assets in Logseq."""

    index: FileIndex
    asset_mapping: dict[str, LogseqFile] = field(default_factory=dict)
    hls_bullets: set[str] = field(default_factory=set)
    backlinked_hls: set[str] = field(default_factory=set)
    not_backlinked_hls: set[str] = field(default_factory=set)
    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)
    _mentioned: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqAssetsHls instance."""
        for f in self.index:
            self._get_asset_file(f)
        if self.asset_mapping:
            for f in self.index:
                self._get_hls_bullet(f)
            self._check_backlinks()
        for f in self.index:
            self._process(f)
        self.backlinked.update(self.index.yield_assets_with_backlink(backlinked=True))
        self.not_backlinked.update(self.index.yield_assets_with_backlink(backlinked=False))

    def _get_asset_file(self, f: LogseqFile) -> None:
        """Get asset files from the index."""
        if f.path.file_type == FileType.SUB_ASSET:
            self.asset_mapping[f.path.name] = f

    def _get_hls_bullet(self, f: LogseqFile) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        if not f.is_hls:
            return
        for bullet in f.bullets.all_bullets:
            if not bullet.strip().startswith("[:span]"):
                continue
            hl_page, id_, hl_stamp = "", "", ""
            for prop_value in ContentPatterns.PROPERTY_VALUE.finditer(bullet):
                propkey = prop_value.group(1)
                value = prop_value.group(2).strip()
                match propkey:
                    case "hl-page":
                        hl_page = value
                    case "id":
                        id_ = value
                    case "hl-stamp":
                        hl_stamp = value
            if all((hl_page, id_, hl_stamp)):
                hls_bullet = f"{hl_page}_{id_}_{hl_stamp}"
                self.hls_bullets.add(hls_bullet)

    def _check_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        _asset_mapping_keys = set(self.asset_mapping.keys())
        for name in self.hls_bullets:
            if not (asset_file := self.asset_mapping.get(name)):
                continue
            asset_file.path.file_type = FileType.ASSET  # TODO: Refactor, mutates file directly
            if name in _asset_mapping_keys:
                _asset_mapping_keys.remove(name)
                self.backlinked_hls.add(name)
                asset_file.node.backlinked = True  # TODO: Refactor, mutates file directly
            else:
                self.not_backlinked_hls.add(name)

    def _process(self, f: LogseqFile) -> None:
        _is_asset_processed = False
        if not (f_data := f.data):
            return
        for criteria in _ASSET_CRITERIA:
            self._mentioned.update(f_data.get(criteria, []))
        if not self._mentioned:
            return
        for file in self.index.yield_assets_with_backlink(backlinked=False):
            self._update_asset_backlink(file, f.path.name)
            _is_asset_processed = True
        if not _is_asset_processed:
            return
        self._mentioned.clear()
        return

    def _update_asset_backlink(self, file: LogseqFile, target_name: str) -> None:
        """Update the asset backlink information."""
        for mention in self._mentioned:
            if any(name in mention for name in (file.path.name, target_name)):
                file.node.backlinked = True  # TODO: Refactor, mutates file directly
                return

    @property
    def report(self) -> dict[str, object]:
        """Generate a report of the asset analysis."""
        return {
            OutputDir.ASSETS: {
                Output.HLS_ASSET_MAPPING: self.asset_mapping,
                Output.HLS_FORMATTED_BULLETS: self.hls_bullets,
                Output.HLS_NOT_BACKLINKED: self.not_backlinked_hls,
                Output.HLS_BACKLINKED: self.backlinked_hls,
                Output.ASSETS_BACKLINKED: self.backlinked,
                Output.ASSETS_NOT_BACKLINKED: self.not_backlinked,
            },
        }


"""Logseq Content Summarizer Module."""


@dataclass(slots=True)
class LogseqSummarizer:
    """Class to summarize Logseq analysis."""

    index: FileIndex
    file: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extensions: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    content: dict[str, dict[str, dict[str, object]]] = field(default_factory=dict)
    content_info: dict[str, dict[str, object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqSummarizer instance."""
        for f in self.index:
            self._process(f)
        for k, v in self.file.items():
            self.file[k] = sorted(v)
        for k, v in self.content.items():
            if k != "_info":
                self.content[k] = sort_dict_by_value(v, value="count", reverse=True)

    def _process(self, f: LogseqFile) -> None:
        """Process a file for summarization."""
        self.filetypes[f.path.file_type].append(f.path.name)
        self.nodetypes[f.node.node_type].append(f.path.name)
        self.extensions[f.path.file.suffix].append(f.path.name)
        if f.node.backlinked:
            self.file[Output.SUMMARY_BACKLINKED].append(f.path.name)
        if f.node.backlinked_ns_only:
            self.file[Output.SUMMARY_BACKLINKED_NS_ONLY].append(f.path.name)
        if f.is_hls:
            self.file[Output.SUMMARY_IS_HLS].append(f.path.name)
        if f.info.size.has_content:
            self.file[Output.SUMMARY_HAS_CONTENT].append(f.path.name)
        if f.node.has_backlinks:
            self.file[Output.SUMMARY_HAS_BACKLINKS].append(f.path.name)
        for k, v in f.data.items():
            self.content.setdefault(k, {})
            self.content[k] = get_count_and_foundin_data(self.content[k], v, f.path.name)
        self.content_info.setdefault("info", {})
        self.content_info["info"][f.path.name] = {
            Output.SUMMARY_REPORT_BULLET: f.info.bullet,
            Output.SUMMARY_REPORT_NAMESPACE: f.info.namespace,
            Output.SUMMARY_REPORT_SIZE: f.info.size,
            Output.SUMMARY_REPORT_TIMESTAMP: f.info.timestamp,
        }

    @property
    def report(self) -> dict[str, object]:
        """Generate a report of the summarization."""
        return {
            OutputDir.SUMMARY_FILE_GENERAL: self.file,
            OutputDir.SUMMARY_FILE_FILETYPE: self.filetypes,
            OutputDir.SUMMARY_FILE_NODETYPE: self.nodetypes,
            OutputDir.SUMMARY_FILE_EXTENSION: self.extensions,
            OutputDir.SUMMARY_CONTENT: self.content,
            OutputDir.SUMMARY_CONTENT_INFO: self.content_info,
        }
