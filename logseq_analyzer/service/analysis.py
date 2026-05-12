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
from enum import IntEnum
from itertools import chain
from typing import TYPE_CHECKING, TypedDict

from logseq_analyzer.utils.enums import Core, Crit, FileType, Output, OutputDir
from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES, get_count_and_foundin_data, sort_dict_by_value
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from logseq_analyzer.domain.model import FileIndex, LogseqFile

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
        for values in self.all_linked_refs.values():
            found_in_map = values.get("found_in", {})
            values["found_in"] = sort_dict_by_value(found_in_map, reverse=True)
        self.all_linked_refs = sort_dict_by_value(self.all_linked_refs, value="count", reverse=True)
        self.dangling_links = (
            (self.linked_refs | self.linked_refs_ns)
            - set(self.index.yield_names())
            - self.aliases
            - BUILT_IN_PROPERTIES
        )
        self.all_dangling_links = {k: v for k, v in self.all_linked_refs.items() if k in self.dangling_links}

    def _process_content(self, f: LogseqFile) -> None:
        if f.ns_info.is_namespace:
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
        if f.ns_info.parent:
            lr_with_ns_parent = [*_linkedrefs, f.ns_info.parent]
            self.all_linked_refs = get_count_and_foundin_data(self.all_linked_refs, lr_with_ns_parent, f.name)
        else:
            self.all_linked_refs = get_count_and_foundin_data(self.all_linked_refs, _linkedrefs, f.name)
        self.linked_refs.update(_linkedrefs)

    def _process_namespaces(self, f: LogseqFile) -> None:
        """Post-process namespaces in the content data."""
        self.linked_refs_ns.update((f.ns_info.root, f.name))
        for ns_root in self.index.get_from_name(f.ns_info.root):
            ns_root.ns_info.is_namespace = True  # TODO: Refactor, mutates file directly
            ns_root.ns_info.children.add(f.name)  # TODO: Refactor, mutates file directly
        for ns_parent in self.index.get_from_name(f.ns_info.parent_full):
            ns_parent.ns_info.children.add(f.name)  # TODO: Refactor, mutates file directly

    def _process_nodes(self, f: LogseqFile) -> None:
        """Process summary data for a single file based on metadata and content analysis."""
        if f.name in self.linked_refs:
            self.linked_refs.remove(f.name)
            f.node.backlinked = True  # TODO: Refactor, mutates file directly
        if f.name in self.linked_refs_ns:
            self.linked_refs_ns.remove(f.name)
            if not f.node.backlinked_ns_only:
                f.node.backlinked_ns_only = True  # TODO: Refactor, mutates file directly
                f.node.backlinked = False  # TODO: Refactor, mutates file directly
        if f.filetype in _TO_NODE_TYPE:
            f.node.determine_node_type(has_content=f.file_info.has_content)  # TODO: Refactor, mutates file directly

    @property
    def report(self) -> dict:
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
    details: dict[str, Counter[int]] = field(default_factory=dict)
    parts: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    tree: _NsTree = field(default_factory=dict)
    unique_ns_per_level: dict[int, set[str]] = field(default_factory=lambda: defaultdict(set))
    unique_parts: set[str] = field(default_factory=set)
    queries: dict[str, _QueryInfo] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqNamespaces instance."""
        self.details["level_distribution"] = Counter()
        for f in self.index:
            self._process(f)
        self.queries = sort_dict_by_value(self.queries, value="size", reverse=True)
        self.analyze_ns_conflicts()

    def _process(self, f: LogseqFile) -> None:
        """Initialize namespace parts for a given file."""
        if not f.ns_info.is_namespace:
            return
        if not (parts := f.ns_info.parts):
            return
        cur = self.tree
        for part, level in parts:
            self.parts[f.name].append(part)
            self.unique_parts.add(part)
            self.unique_ns_per_level[level].add(part)
            self.details["level_distribution"][level] += 1
            self._part_levels[part].add(level)
            self._part_entries[part].append({"entry": f.name, "level": level})
            cur = cur.setdefault(part, {})
        for query in f.data.get(Crit.DblCurly.NAMESPACE_QUERY, ()):
            page_refs: list[str] = ContentPatterns.PAGE_REFERENCE.findall(query)
            if len(page_refs) != 1:
                logger.warning("Invalid query: %s", query)
                continue
            if query in self.queries:
                self.queries[query]["found_in"].append(f.name)
            else:
                self.queries[query] = {
                    "found_in": [f.name],
                    "namespace": page_refs[0],
                    "size": f.ns_info.size,
                    "uri": f.uri,
                    "logseq_url": f.ls_url,
                }

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
    def report(self) -> dict:
        """Generate a report of the namespace analysis."""
        return {
            OutputDir.NAMESPACES: {
                Output.NS_CONFLICTS_DANGLING: self.conflicts_dangling,
                Output.NS_CONFLICTS_NON_NAMESPACE: self.conflicts_non_namespace,
                Output.NS_CONFLICTS_PARENT_DEPTH: self.conflicts_parent_depth,
                Output.NS_CONFLICTS_PARENT_UNIQUE: self.conflicts_parent_unique,
                Output.NS_DETAILS: self.details,
                Output.NS_HIERARCHY: self.tree,
                Output.NS_PARTS: self.parts,
                Output.NS_UNIQUE_PARTS: self.unique_parts,
                Output.NS_UNIQUE_PER_LEVEL: self.unique_ns_per_level,
                Output.NS_QUERIES: self.queries,
            }
        }


def _asset_criteria() -> frozenset[str]:
    """Return the criteria for identifying assets in Logseq content."""
    return frozenset((Crit.Emb.ASSET, Crit.Content.ASSETS))


@dataclass(slots=True)
class LogseqAssets:
    """Analyze assets in Logseq."""

    index: FileIndex
    _mentions: set[str] = field(default_factory=set)
    _criteria: frozenset[str] = field(default_factory=_asset_criteria)
    asset_mapping: dict[str, LogseqFile] = field(default_factory=dict)
    hls_bullets: set[str] = field(default_factory=set)
    backlinked_hls: set[str] = field(default_factory=set)
    not_backlinked_hls: set[str] = field(default_factory=set)
    backlinked: set[str] = field(default_factory=set)
    not_backlinked: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        for f in self.index:
            self._get_asset_file(f)
            self._get_hls_bullet(f)
        if self.asset_mapping:
            self._check_backlinks()
        for f in self.index:
            self._process(f)
        self.backlinked.update(self.index.yield_backlinked_assets_name(backlinked=True))
        self.not_backlinked.update(self.index.yield_backlinked_assets_name(backlinked=False))

    def _get_asset_file(self, f: LogseqFile) -> None:
        """Get asset files from the index."""
        if f.filetype == FileType.SUB_ASSET:
            self.asset_mapping[f.name] = f

    def _get_hls_bullet(self, f: LogseqFile) -> None:
        """Extract HLS bullets from a file and add them to the set of HLS bullets."""
        if not f.is_hls:
            return
        for bullet in f.all_bullets:
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
                self.hls_bullets.add(f"{hl_page}_{id_}_{hl_stamp}")

    def _check_backlinks(self) -> None:  # TODO: Refactor, mutates file directly
        """Check for backlinks in the HLS assets."""
        remaining = set(self.asset_mapping.keys())
        for name in self.hls_bullets:
            if not (asset_file := self.asset_mapping.get(name)):
                continue
            asset_file.filetype = FileType.ASSET  # TODO: Refactor
            if name in remaining:
                remaining.discard(name)
                self.backlinked_hls.add(name)
                asset_file.node.backlinked = True  # TODO: Refactor
            else:
                self.not_backlinked_hls.add(name)

    def _process(self, f: LogseqFile) -> None:  # TODO: Refactor, mutates file directly
        _is_asset_processed = False
        if not (f_data := f.data):
            return
        for criteria in self._criteria:
            self._mentions.update(f_data.get(criteria, []))
        if not self._mentions:
            return
        for unlinked_asset in self.index.yield_backlinked_assets(backlinked=False):
            for mention in self._mentions:
                if any(name in mention for name in (unlinked_asset.name, f.name)):
                    unlinked_asset.node.backlinked = True  # TODO: Refactor
                    break
            _is_asset_processed = True
        if not _is_asset_processed:
            return
        self._mentions.clear()

    @property
    def report(self) -> dict:
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
        fmt = self.journal_page_format.replace("#", "")
        for key in keys:
            try:
                key_to_parse = key
                for ordinal in _DATE_ORDINAL_SUFFIXES:
                    key_to_parse = key_to_parse.replace(ordinal, "")
                yield datetime.strptime(key_to_parse, fmt).replace(tzinfo=UTC)
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
        self.stat["timeline"] = _get_journal_stats(self.timeline)
        self.stat["dangling"] = _get_journal_stats(dangling_dt)
        self.stat["total"] = _get_journal_stats(self.all_)
        for link in dangling_dt:
            if link < self.stat["timeline"]["first"]:
                self.dangling["past"].append(link)
            elif link > self.stat["timeline"]["last"]:
                self.dangling["future"].append(link)
            else:
                self.dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, dict[str, object]]:
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


@dataclass(slots=True)
class LogseqSummarizer:
    """Summarize Logseq analysis."""

    index: FileIndex
    file: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetype: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetype: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extension: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    content: dict[str, dict[str, dict[str, object]]] = field(default_factory=dict)
    info: dict[str, dict[str, object]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqSummarizer instance."""
        for f in self.index:
            self._process(f)
        for k, v in self.file.items():
            self.file[k] = sorted(v)
        for k, v in self.content.items():
            self.content[k] = sort_dict_by_value(v, value="count", reverse=True)

    def _process(self, f: LogseqFile) -> None:
        """Process a file for summarization."""
        self.filetype[f.filetype].append(f.name)
        self.nodetype[f.node.nodetype].append(f.name)
        self.extension[f.path.suffix].append(f.name)
        if f.node.backlinked:
            self.file[Output.SUMMARY_BACKLINKED].append(f.name)
        if f.node.backlinked_ns_only:
            self.file[Output.SUMMARY_BACKLINKED_NS_ONLY].append(f.name)
        if f.is_hls:
            self.file[Output.SUMMARY_IS_HLS].append(f.name)
        if f.file_info.has_content:
            self.file[Output.SUMMARY_HAS_CONTENT].append(f.name)
        if f.node.has_backlinks:
            self.file[Output.SUMMARY_HAS_BACKLINKS].append(f.name)
        for k, v in f.data.items():
            self.content.setdefault(k, {})
            self.content[k] = get_count_and_foundin_data(self.content[k], v, f.name)
        self.info.setdefault("info", {})
        self.info["info"][f.name] = {
            Output.SUMMARY_REPORT_BULLET: f.bullet_info,
            Output.SUMMARY_REPORT_NAMESPACE: f.ns_info,
            Output.SUMMARY_REPORT_FILE_INFO: f.file_info,
        }

    @property
    def report(self) -> dict:
        """Generate a report of the summarization."""
        return {
            OutputDir.SUMMARY_FILE_GENERAL: self.file,
            OutputDir.SUMMARY_FILE_FILETYPE: self.filetype,
            OutputDir.SUMMARY_FILE_NODETYPE: self.nodetype,
            OutputDir.SUMMARY_FILE_EXTENSION: self.extension,
            OutputDir.SUMMARY_CONTENT: self.content,
            OutputDir.SUMMARY_CONTENT_INFO: self.info,
        }
