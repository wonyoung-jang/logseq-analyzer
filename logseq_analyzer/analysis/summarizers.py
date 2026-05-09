"""Logseq Content Summarizer Module."""

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from logseq_analyzer.utils.enums import OutputDir
from logseq_analyzer.utils.helpers import get_count_and_foundin_data, sort_dict_by_value

if TYPE_CHECKING:
    from logseq_analyzer.analysis.file import LogseqFile
    from logseq_analyzer.analysis.index import FileIndex


class SummaryFile(StrEnum):
    """Summary files for the Logseq Analyzer."""

    BACKLINKED = "backlinked"
    BACKLINKED_NS_ONLY = "backlinked_ns_only"
    HAS_BACKLINKS = "has_backlinks"
    HAS_CONTENT = "has_content"
    IS_HLS = "is_hls"
    REPORT_SIZE = "report_size"
    REPORT_TIMESTAMP = "report_timestamp"
    REPORT_NAMESPACE = "report_namespace"
    REPORT_BULLET = "report_bullet"


@dataclass(slots=True)
class LogseqSummarizer:
    """Class to summarize Logseq analysis."""

    index: FileIndex
    file: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    filetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    nodetypes: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    extensions: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    content: dict[str, dict[str, Any]] = field(default_factory=dict)
    size_report: dict[str, Any] = field(default_factory=dict)
    timestamp_report: dict[str, Any] = field(default_factory=dict)
    namespace_report: dict[str, Any] = field(default_factory=dict)
    bullet_report: dict[str, Any] = field(default_factory=dict)

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
        self.filetypes[f.path.file_type].append(f.path.name)
        self.nodetypes[f.node.node_type].append(f.path.name)
        self.extensions[f.path.file.suffix].append(f.path.name)
        if f.node.backlinked:
            self.file[SummaryFile.BACKLINKED].append(f.path.name)
        if f.node.backlinked_ns_only:
            self.file[SummaryFile.BACKLINKED_NS_ONLY].append(f.path.name)
        if f.is_hls:
            self.file[SummaryFile.IS_HLS].append(f.path.name)
        if f.info.size.has_content:
            self.file[SummaryFile.HAS_CONTENT].append(f.path.name)
        if f.node.has_backlinks:
            self.file[SummaryFile.HAS_BACKLINKS].append(f.path.name)
        for k, v in f.data.items():
            self.content.setdefault(k, {})
            self.content[k] = get_count_and_foundin_data(self.content[k], v, f.path.name)
        self.size_report[f.path.name] = f.info.size
        self.timestamp_report[f.path.name] = f.info.timestamp
        self.namespace_report[f.path.name] = f.info.namespace
        self.bullet_report[f.path.name] = f.info.bullet

    @property
    def report(self) -> dict:
        """Generate a report of the summarization."""
        return {
            OutputDir.SUMMARY_FILES_GENERAL: self.file,
            OutputDir.SUMMARY_FILES_FILE: self.filetypes,
            OutputDir.SUMMARY_FILES_NODE: self.nodetypes,
            OutputDir.SUMMARY_FILES_EXTENSIONS: self.extensions,
            OutputDir.SUMMARY_CONTENT: self.content,
            OutputDir.SUMMARY_CONTENT_INFO: {
                SummaryFile.REPORT_SIZE: self.size_report,
                SummaryFile.REPORT_TIMESTAMP: self.timestamp_report,
                SummaryFile.REPORT_NAMESPACE: self.namespace_report,
                SummaryFile.REPORT_BULLET: self.bullet_report,
            },
        }
