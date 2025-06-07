"""
Process logseq journals.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..analysis.index import FileIndex
from ..utils.date_utilities import DateUtilities
from ..utils.enums import FileType, Output

__all__ = [
    "LogseqJournals",
]


@dataclass
class JournalSets:
    """Class to hold sets of journal dates."""

    all_journals: list[datetime] = field(default_factory=list)
    existing: list[datetime] = field(default_factory=list)
    missing: list[datetime] = field(default_factory=list)
    timeline: list[datetime] = field(default_factory=list)


class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    __slots__ = (
        "dangling",
        "timeline_stats",
        "sets",
        "index",
        "dangling_links",
    )

    journal_page_format: str = ""

    def __init__(self, index: FileIndex, dangling_links: set[str]) -> None:
        """Initialize the LogseqJournals class."""
        self.sets: JournalSets = JournalSets()
        self.dangling: dict[str, list[datetime]] = defaultdict(list)
        self.timeline_stats: dict[str, Any] = {}
        self.index: FileIndex = index
        self.dangling_links: set[str] = dangling_links
        self.process()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}"

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.sets.timeline)

    def process(self, journal_file: str = FileType.JOURNAL) -> None:
        """Process journal keys to build the complete timeline and detect missing entries."""
        index = self.index
        page_format = LogseqJournals.journal_page_format
        dangling = sorted(DateUtilities.journals_to_datetime(self.dangling_links, page_format))
        journals = (f.path.name for f in index if f.path.file_type == journal_file)
        self.sets.existing.extend(sorted(DateUtilities.journals_to_datetime(journals, page_format)))
        self.build_complete_timeline(dangling)
        self.get_dangling_journals_outside_range(dangling)

    def build_complete_timeline(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        existing = self.sets.existing
        timeline = self.sets.timeline
        append_missing = self.sets.missing.append
        append_timeline = timeline.append
        get_stats = DateUtilities.stats
        next_date = DateUtilities.next
        for i, date in enumerate(existing):
            append_timeline(date)
            next_expected = next_date(date)
            next_existing = existing[i + 1] if i + 1 < len(existing) else None
            while next_existing and next_expected < next_existing:
                append_timeline(next_expected)
                if next_expected not in dangling_journals:
                    append_missing(next_expected)
                next_expected = next_date(next_expected)
        self.sets.all_journals = sorted(timeline + dangling_journals)
        self.timeline_stats = {
            "timeline": get_stats(timeline),
            "dangling": get_stats(dangling_journals),
            "total": get_stats(self.sets.all_journals),
        }

    def get_dangling_journals_outside_range(self, dangling_journals: list[datetime]) -> None:
        """Check for dangling journals that are outside the range of the complete timeline."""
        append_dangling_past = self.dangling["past"].append
        append_dangling_future = self.dangling["future"].append
        append_dangling_inside = self.dangling["inside"].append
        first_date = self.timeline_stats["timeline"]["first"]
        last_date = self.timeline_stats["timeline"]["last"]
        for link in dangling_journals:
            if link < first_date:
                append_dangling_past(link)
            elif link > last_date:
                append_dangling_future(link)
            else:
                append_dangling_inside(link)

    @property
    def report(self) -> dict[str, Any]:
        """Get a report of the journal processing results."""
        return {
            Output.JOURNALS_ALL: self.sets.all_journals,
            Output.JOURNALS_DANGLING: self.dangling,
            Output.JOURNALS_EXISTING: self.sets.existing,
            Output.JOURNALS_TIMELINE: self.sets.timeline,
            Output.JOURNALS_MISSING: self.sets.missing,
            Output.JOURNALS_TIMELINE_STATS: self.timeline_stats,
        }
