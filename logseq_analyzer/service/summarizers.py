"""Logseq Content Summarizer Module."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from logseq_analyzer.utils.enums import Output, OutputDir
from logseq_analyzer.utils.helpers import get_count_and_foundin_data, sort_dict_by_value

if TYPE_CHECKING:
    from logseq_analyzer.domain.file import LogseqFile
    from logseq_analyzer.domain.index import FileIndex


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
