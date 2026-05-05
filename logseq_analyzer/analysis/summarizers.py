"""Logseq Content Summarizer Module."""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from logseq_analyzer.utils.helpers import get_count_and_foundin_data, sort_dict_by_value

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex


class SummaryFile(StrEnum):
    """Summary files for the Logseq Analyzer."""

    BACKLINKED = "backlinked"
    BACKLINKED_NS_ONLY = "backlinked_ns_only"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_HLS = "is_hls"


@dataclass(slots=True)
class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    index: FileIndex
    general: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extensions: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        for f in self.index:
            self.filetypes[f.path.file_type].append(f.path.name)
            self.nodetypes[f.node.node_type].append(f.path.name)
            self.extensions[f.path.file.suffix].append(f.path.name)
            if f.node.backlinked:
                self.general[SummaryFile.BACKLINKED].append(f.path.name)
            if f.node.backlinked_ns_only:
                self.general[SummaryFile.BACKLINKED_NS_ONLY].append(f.path.name)
            if f.is_hls:
                self.general[SummaryFile.IS_HLS].append(f.path.name)
            if f.info.size.has_content:
                self.general[SummaryFile.HAS_CONTENT].append(f.path.name)
            if f.node.has_backlinks:
                self.general[SummaryFile.HAS_BACKLINKS].append(f.path.name)
        for k, v in self.general.items():
            self.general[k] = sorted(v)


@dataclass(slots=True)
class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    index: FileIndex
    report: dict[str, dict[str, Any]] = field(default_factory=dict)
    size_report: dict[str, dict[str, Any]] = field(default_factory=dict)
    timestamp_report: dict[str, dict[str, Any]] = field(default_factory=dict)
    namespace_report: dict[str, dict[str, Any]] = field(default_factory=dict)
    bullet_report: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.size_report["report_size"] = {}
        self.timestamp_report["report_timestamp"] = {}
        self.namespace_report["report_namespace"] = {}
        self.bullet_report["report_bullet"] = {}
        for f in self.index:
            for k, v in f.data.items():
                self.report.setdefault(k, {})
                self.report[k] = get_count_and_foundin_data(self.report[k], v, f.path.name)
            self.size_report["report_size"][f.path.name] = f.info.size
            self.timestamp_report["report_timestamp"][f.path.name] = f.info.timestamp
            self.namespace_report["report_namespace"][f.path.name] = f.info.namespace
            self.bullet_report["report_bullet"][f.path.name] = f.info.bullet
        for k in self.report:
            self.report[k] = sort_dict_by_value(self.report[k], value="count", reverse=True)
