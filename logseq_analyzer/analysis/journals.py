"""Process logseq journals."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from logseq_analyzer.utils.date_utilities import DateUtilities
from logseq_analyzer.utils.enums import FileType, Output

if TYPE_CHECKING:
    from datetime import datetime

    from logseq_analyzer.analysis.index import FileIndex


@dataclass(slots=True)
class LogseqJournals:
    """LogseqJournals class to handle journal files and their processing."""

    index: FileIndex
    dangling_links: set[str]
    all_journals: list[datetime] = field(default_factory=list)
    existing: list[datetime] = field(default_factory=list)
    missing: list[datetime] = field(default_factory=list)
    timeline: list[datetime] = field(default_factory=list)
    dangling: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))
    timeline_stats: dict[str, Any] = field(default_factory=dict)
    journal_page_format: ClassVar[str] = ""

    def __post_init__(self) -> None:
        """Initialize the LogseqJournals class."""
        dangling = sorted(DateUtilities.journals_to_datetime(self.dangling_links, LogseqJournals.journal_page_format))
        journals = (f.path.name for f in self.index if f.path.file_type == FileType.JOURNAL)
        self.existing.extend(sorted(DateUtilities.journals_to_datetime(journals, LogseqJournals.journal_page_format)))
        self.build_complete_timeline(dangling)
        self.get_dangling_journals_outside_range(dangling)

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.timeline)

    def build_complete_timeline(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        for i, date in enumerate(self.existing):
            self.timeline.append(date)
            next_expected = DateUtilities.next(date)
            next_existing = self.existing[i + 1] if i + 1 < len(self.existing) else None
            while next_existing and next_expected < next_existing:
                self.timeline.append(next_expected)
                if next_expected not in dangling_journals:
                    self.missing.append(next_expected)
                next_expected = DateUtilities.next(next_expected)
        self.all_journals = sorted(self.timeline + dangling_journals)
        self.timeline_stats = {
            "timeline": DateUtilities.stats(self.timeline),
            "dangling": DateUtilities.stats(dangling_journals),
            "total": DateUtilities.stats(self.all_journals),
        }

    def get_dangling_journals_outside_range(self, dangling_journals: list[datetime]) -> None:
        """Check for dangling journals that are outside the range of the complete timeline."""
        for link in dangling_journals:
            if link < self.timeline_stats["timeline"]["first"]:
                self.dangling["past"].append(link)
            elif link > self.timeline_stats["timeline"]["last"]:
                self.dangling["future"].append(link)
            else:
                self.dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, Any]:
        """Get a report of the journal processing results."""
        return {
            Output.JOURNALS_ALL: self.all_journals,
            Output.JOURNALS_DANGLING: self.dangling,
            Output.JOURNALS_EXISTING: self.existing,
            Output.JOURNALS_TIMELINE: self.timeline,
            Output.JOURNALS_MISSING: self.missing,
            Output.JOURNALS_TIMELINE_STATS: self.timeline_stats,
        }
