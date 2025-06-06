"""
Logseq Content Summarizer Module
"""

from collections import defaultdict
from enum import StrEnum
from typing import Any

from ..utils.helpers import get_count_and_foundin_data, sort_dict_by_value
from .index import FileIndex

__all__ = [
    "LogseqFileSummarizer",
    "LogseqContentSummarizer",
    "SummaryFile",
]


class SummaryFile(StrEnum):
    """Summary files for the Logseq Analyzer."""

    BACKLINKED = "backlinked"
    BACKLINKED_NS_ONLY = "backlinked_ns_only"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_HLS = "is_hls"


class LogseqFileSummarizer:
    """Class to summarize Logseq files."""

    __slots__ = (
        "index",
        "general",
        "filetypes",
        "nodetypes",
        "extensions",
    )

    def __init__(self, index: FileIndex) -> None:
        """Initialize the LogseqFileSummarizer instance."""
        self.index: FileIndex = index
        self.general: dict[str, list[str]] = defaultdict(list)
        self.filetypes: dict[str, list[str]] = defaultdict(list)
        self.nodetypes: dict[str, list[str]] = defaultdict(list)
        self.extensions: dict[str, list[str]] = defaultdict(list)
        self.process()

    def process(self) -> None:
        """Generate summary subsets for the Logseq Analyzer."""
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


class LogseqContentSummarizer:
    """Class to summarize Logseq content."""

    __slots__ = ("report", "index", "size_report", "timestamp_report", "namespace_report", "bullet_report")

    def __init__(self, index: FileIndex) -> None:
        """Initialize the LogseqContentSummarizer instance."""
        self.index: FileIndex = index
        self.report: dict[str, dict[str, Any]] = {}
        self.size_report: dict[str, dict[str, Any]] = {}
        self.timestamp_report: dict[str, dict[str, Any]] = {}
        self.namespace_report: dict[str, dict[str, Any]] = {}
        self.bullet_report: dict[str, dict[str, Any]] = {}
        self.process()

    def process(self) -> None:
        """Process the Logseq content data."""
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
            if f_data := f.data:
                for k, v in f_data.items():
                    report.setdefault(k, {})
                    report[k] = get_count_and_foundin_data(report[k], v, f_name)
            if f_sz := f_info.size:
                sz_report[f_name] = f_sz.__dict__
            if f_ts := f_info.timestamp:
                ts_report[f_name] = f_ts.__dict__
            if f_ns := f_info.namespace:
                ns_report[f_name] = f_ns.__dict__
            if f_bt := f_info.bullet:
                bt_report[f_name] = f_bt.__dict__
        self.size_report = {"report_size": sz_report}
        self.timestamp_report = {"report_timestamp": ts_report}
        self.namespace_report = {"report_namespace": ns_report}
        self.bullet_report = {"report_bullet": bt_report}

    def sort_report(self) -> None:
        """Sort the report dictionary by count in descending order."""
        report = self.report
        for k in report:
            report[k] = sort_dict_by_value(report[k], value="count", reverse=True)
