"""Logseq Content Summarizer Module."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..utils.helpers import get_count_and_foundin_data, sort_dict_by_value
from .index import FileIndex

__all__ = [
    "LogseqContentSummarizer",
    "LogseqFileSummarizer",
    "SummaryFile",
]


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

    index: FileIndex = field(default_factory=FileIndex)
    general: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extensions: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    def __post_init__(self) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.generate_summary()

    def generate_summary(self) -> None:
        """Generate general subsets for the Logseq Analyzer."""
        general = self.general
        filetypes = self.filetypes
        nodetypes = self.nodetypes
        extensions = self.extensions
        for f in self.index:
            f_node = f.node
            f_path = f.path
            f_name = f_path.name
            filetypes[f_path.file_type].append(f_name)
            nodetypes[f_node.node_type].append(f_name)
            extensions[f_path.file.suffix].append(f_name)

            if f_node.backlinked:
                general[SummaryFile.BACKLINKED].append(f_name)

            if f_node.backlinked_ns_only:
                general[SummaryFile.BACKLINKED_NS_ONLY].append(f_name)

            if f.is_hls:
                general[SummaryFile.IS_HLS].append(f_name)

            if f.info.size.has_content:
                general[SummaryFile.HAS_CONTENT].append(f_name)

            if f_node.has_backlinks:
                general[SummaryFile.HAS_BACKLINKS].append(f_name)

        for k, v in general.items():
            general[k] = sorted(v)


@dataclass(slots=True)
class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    index: FileIndex = field(default_factory=FileIndex)
    report: dict[str, dict[str, Any]] = field(default_factory=dict)
    size_report: dict[str, dict[str, Any]] = field(default_factory=dict)
    timestamp_report: dict[str, dict[str, Any]] = field(default_factory=dict)
    namespace_report: dict[str, dict[str, Any]] = field(default_factory=dict)
    bullet_report: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.generate_summary()
        self.sort_report()

    def generate_summary(self) -> None:
        """Generate summary subsets for content data in the Logseq graph."""
        sz_report = {}
        ts_report = {}
        ns_report = {}
        bt_report = {}
        report = self.report
        for f in self.index:
            f_name = f.path.name
            f_info = f.info
            for k, v in f.data.items():
                report.setdefault(k, {})
                report[k] = get_count_and_foundin_data(report[k], v, f_name)
            sz_report[f_name] = f_info.size
            ts_report[f_name] = f_info.timestamp
            ns_report[f_name] = f_info.namespace
            bt_report[f_name] = f_info.bullet
        self.size_report = {"report_size": sz_report}
        self.timestamp_report = {"report_timestamp": ts_report}
        self.namespace_report = {"report_namespace": ns_report}
        self.bullet_report = {"report_bullet": bt_report}

    def sort_report(self) -> None:
        """Sort the report dictionary by count in descending order."""
        report = self.report
        for k in report:
            report[k] = sort_dict_by_value(report[k], value="count", reverse=True)
