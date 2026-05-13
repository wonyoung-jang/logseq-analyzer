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

import contextlib
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum
from itertools import chain
from typing import TYPE_CHECKING, TypedDict

from logseq_analyzer.domain.model import BUILT_IN_PROPERTIES
from logseq_analyzer.utils.enums import Core, Crit, FileType, Output
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from logseq_analyzer.domain.model import FileIndex, LogseqFile

logger = logging.getLogger(__name__)

_TO_NODE_TYPE: frozenset[str] = frozenset((FileType.JOURNAL, FileType.PAGE))
_ASSET_CRITERIA: frozenset[str] = frozenset((Crit.Emb.ASSET, Crit.Content.ASSETS))
_DATE_ORDINAL_SUFFIXES: frozenset[str] = frozenset(("st", "nd", "rd", "th"))

type _NsTree = dict[str, "_NsTree"]


class Day(IntEnum):
    """Enum for days of the week."""

    IN_WEEK = 7
    IN_MONTH = 30
    IN_YEAR = 365


class _QueryInfo(TypedDict, total=False):
    found_in: list[str]
    namespace: str
    size: int
    uri: str
    logseq_url: str


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


@dataclass(slots=True)
class LogseqGraph:
    """Class to handle all Logseq files in the graph directory."""

    index: FileIndex
    dangling_links: set[str] = field(default_factory=set)
    dangling_links_count: dict = field(default_factory=dict)
    linked_refs: set[str] = field(default_factory=set)
    linked_refs_ns: set[str] = field(default_factory=set)
    linked_refs_count: dict = field(default_factory=dict)
    aliases: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqGraph instance."""
        for f in self.index:
            self._process_content(f)
        for f in self.index:
            self._process_nodes(f)
        self.dangling_links = (
            (self.linked_refs | self.linked_refs_ns)
            - set(self.index.yield_names())
            - self.aliases
            - BUILT_IN_PROPERTIES
        )
        self.dangling_links_count = {k: v for k, v in self.linked_refs_count.items() if k in self.dangling_links}

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
            _update_counts(self.linked_refs_count, lr_with_ns_parent, f.name)
        else:
            _update_counts(self.linked_refs_count, _linkedrefs, f.name)
        self.linked_refs.update(_linkedrefs)

    def _process_namespaces(self, f: LogseqFile) -> None:  # TODO: Refactor, mutates file directly
        """Post-process namespaces in the content data."""
        self.linked_refs_ns.update((f.ns_info.root, f.name))
        for ns_root in self.index.get_from_name(f.ns_info.root):
            ns_root.ns_info.is_namespace = True  # TODO: Refactor
            ns_root.ns_info.children.add(f.name)  # TODO: Refactor
        for ns_parent in self.index.get_from_name(f.ns_info.parent_full):
            ns_parent.ns_info.children.add(f.name)  # TODO: Refactor

    def _process_nodes(self, f: LogseqFile) -> None:  # TODO: Refactor, mutates file directly
        """Process summary data for a single file based on metadata and content analysis."""
        if f.name in self.linked_refs:
            self.linked_refs.remove(f.name)
            f.node.backlinked = True  # TODO: Refactor
        if f.name in self.linked_refs_ns:
            self.linked_refs_ns.remove(f.name)
            if not f.node.backlinked_ns_only:
                f.node.backlinked_ns_only = True  # TODO: Refactor
                f.node.backlinked = False  # TODO: Refactor
        if f.filetype in _TO_NODE_TYPE:
            f.node.determine(has_content=f.file_info.has_content)  # TODO: Refactor

    @property
    def report(self) -> dict:
        """Generate a report of the graph analysis."""
        return {
            Output.Dir.GRAPH: {
                Output.File.GRAPH_ALL_LINKED_REFERENCES: self.linked_refs_count,
                Output.File.GRAPH_ALL_DANGLING_LINKS: self.dangling_links_count,
                Output.File.GRAPH_DANGLING_LINKS: self.dangling_links,
                Output.File.GRAPH_UNIQUE_ALIASES: self.aliases,
                Output.File.GRAPH_UNIQUE_LINKED_REFERENCES_NS: self.linked_refs_ns,
                Output.File.GRAPH_UNIQUE_LINKED_REFERENCES: self.linked_refs,
            }
        }


@dataclass(slots=True)
class LogseqAssets:
    """Analyze assets in Logseq."""

    index: FileIndex
    _mentions: set[str] = field(default_factory=set)
    asset_mapping: dict[str, LogseqFile] = field(default_factory=dict)
    hls_bullets: set[str] = field(default_factory=set)
    backlinked_hls: set[str] = field(default_factory=set)
    not_backlinked_hls: set[str] = field(default_factory=set)
    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        for f in self.index:
            self._build_asset_map(f)
            self._get_hls_bullets(f)
        if self.asset_mapping:
            self._process_hls_backlinks()
        for f in self.index:
            self._process_asset(f)
        self.backlinked.update(self.index.yield_backlinked_assets(backlinked=True))
        self.not_backlinked.update(self.index.yield_backlinked_assets(backlinked=False))

    def _build_asset_map(self, f: LogseqFile) -> None:
        """Get asset files from the index."""
        if f.filetype == FileType.SUB_ASSET:
            self.asset_mapping[f.name] = f

    def _get_hls_bullets(self, f: LogseqFile) -> None:
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

    def _process_hls_backlinks(self) -> None:  # TODO: Refactor, mutates file directly
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

    def _process_asset(self, f: LogseqFile) -> None:  # TODO: Refactor, mutates file directly
        """Process a file to find mentions of assets and determine if they are backlinked."""
        if not (f_data := f.data):
            return
        for criteria in _ASSET_CRITERIA:
            self._mentions.update(f_data.get(criteria, []))
        if not self._mentions:
            return
        unlinked_assets = list(self.index.yield_backlinked_assets(backlinked=False))
        if not unlinked_assets:
            return
        for unlinked_asset in unlinked_assets:
            for mention in self._mentions:
                if any(name in mention for name in (unlinked_asset.name, f.name)):
                    unlinked_asset.node.backlinked = True  # TODO: Refactor
                    break
        self._mentions.clear()

    @property
    def report(self) -> dict:
        """Generate a report of the asset analysis."""
        return {
            Output.Dir.ASSETS: {
                Output.File.HLS_ASSET_MAPPING: self.asset_mapping,
                Output.File.HLS_FORMATTED_BULLETS: self.hls_bullets,
                Output.File.HLS_NOT_BACKLINKED: self.not_backlinked_hls,
                Output.File.HLS_BACKLINKED: self.backlinked_hls,
                Output.File.ASSETS_BACKLINKED: self.backlinked,
                Output.File.ASSETS_NOT_BACKLINKED: self.not_backlinked,
            },
        }


@dataclass(slots=True)
class LogseqNamespaces:
    """Class for analyzing namespace data in Logseq."""

    index: FileIndex
    dangling_links: set[str]
    _part_levels: defaultdict[str, set[int]] = field(default_factory=lambda: defaultdict(set))
    _part_entries: defaultdict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
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
            self._part_entries[part].append((f.name, level))
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
            if len(levels) <= 1:
                continue
            for name, level in self._part_entries[part]:
                key = (part, level)
                self.conflicts_parent_unique[key].add(Core.NS_SEP.join(name.split(Core.NS_SEP)[:level]))
                self.conflicts_parent_depth[key].append(name)

    @property
    def report(self) -> dict:
        """Generate a report of the namespace analysis."""
        return {
            Output.Dir.NAMESPACES: {
                Output.File.NS_CONFLICTS_DANGLING: self.conflicts_dangling,
                Output.File.NS_CONFLICTS_NON_NAMESPACE: self.conflicts_non_namespace,
                Output.File.NS_CONFLICTS_PARENT_DEPTH: self.conflicts_parent_depth,
                Output.File.NS_CONFLICTS_PARENT_UNIQUE: self.conflicts_parent_unique,
                Output.File.NS_DETAILS: self.details,
                Output.File.NS_HIERARCHY: self.tree,
                Output.File.NS_PARTS: self.parts,
                Output.File.NS_UNIQUE_PARTS: self.unique_parts,
                Output.File.NS_UNIQUE_PER_LEVEL: self.unique_ns_per_level,
                Output.File.NS_QUERIES: self.queries,
            }
        }


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
        dangling_dt = sorted(self._journals_to_datetime(self.dangling_links))
        self.existing.extend(sorted(self._journals_to_datetime(self.index.yield_journals())))
        self.process(dangling_dt)

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.timeline)

    def _journals_to_datetime(self, keys: Iterable[str]) -> Iterator[datetime]:
        """Convert journal keys from strings to datetime objects."""
        fmt = self.journal_page_format.replace("#", "")
        for key in keys:
            with contextlib.suppress(ValueError):
                key_to_parse = key
                for ordinal in _DATE_ORDINAL_SUFFIXES:
                    key_to_parse = key_to_parse.replace(ordinal, "")
                yield datetime.strptime(key_to_parse, fmt).replace(tzinfo=UTC)

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
            Output.Dir.JOURNALS: {
                Output.File.JOURNALS_ALL: self.all_,
                Output.File.JOURNALS_DANGLING: self.dangling,
                Output.File.JOURNALS_EXISTING: self.existing,
                Output.File.JOURNALS_TIMELINE: self.timeline,
                Output.File.JOURNALS_MISSING: self.missing,
                Output.File.JOURNALS_TIMELINE_STATS: self.stat,
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
    content: dict[str, dict] = field(default_factory=dict)
    info: dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqSummarizer instance."""
        for f in self.index:
            self._process(f)

    def _process(self, f: LogseqFile) -> None:
        """Process a file for summarization."""
        self.filetype[f.filetype].append(f.name)
        self.nodetype[f.node.nodetype].append(f.name)
        self.extension[f.path.suffix].append(f.name)
        if f.node.backlinked:
            self.file[Output.File.SUMMARY_BACKLINKED].append(f.name)
        if f.node.backlinked_ns_only:
            self.file[Output.File.SUMMARY_BACKLINKED_NS_ONLY].append(f.name)
        if f.is_hls:
            self.file[Output.File.SUMMARY_IS_HLS].append(f.name)
        if f.file_info.has_content:
            self.file[Output.File.SUMMARY_HAS_CONTENT].append(f.name)
        if f.node.has_backlinks:
            self.file[Output.File.SUMMARY_HAS_BACKLINKS].append(f.name)
        for k, v in f.data.items():
            data_item = self.content.setdefault(k, {})
            _update_counts(data_item, v, f.name)
        self.info[f.name] = {
            "bullet": f.bullet_info,
            "namespace": f.ns_info,
            "file": f.file_info,
        }

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
