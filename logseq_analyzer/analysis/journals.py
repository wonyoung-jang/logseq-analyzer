"""
Process logseq journals.
"""

from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..utils.date_utilities import DateUtilities
from ..utils.enums import Output, FileTypes
from ..utils.helpers import singleton

if TYPE_CHECKING:
    from ..analysis.index import FileIndex


__all__ = [
    "LogseqJournals",
]


@singleton
class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    __slots__ = (
        "all",
        "dangling",
        "date",
        "existing",
        "missing",
        "timeline_stats",
        "timeline",
    )

    journal_page_format: str = ""

    def __init__(self, date_utilities: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqJournals class."""
        self.all: list[datetime] = []
        self.dangling: dict[str, list[datetime]] = defaultdict(list)
        self.date: DateUtilities = date_utilities
        self.existing: list[datetime] = []
        self.missing: list[datetime] = []
        self.timeline: list[datetime] = []
        self.timeline_stats: dict[str, Any] = {}

    def __repr__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}"

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.timeline)

    def process(self, index: "FileIndex", dangling_links: list[str]) -> None:
        """Process journal keys to build the complete timeline and detect missing entries."""
        journal_page_format = LogseqJournals.journal_page_format
        dangling = sorted(self.date.journals_to_datetime(dangling_links, journal_page_format))
        journal_keys = (f.name for f in index if f.file_type == FileTypes.JOURNAL.value)
        journals = sorted(journal_keys)
        self.existing.extend(sorted(self.date.journals_to_datetime(journals, journal_page_format)))
        self.build_complete_timeline(dangling)
        self.get_dangling_journals_outside_range(dangling)

    def build_complete_timeline(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        existing = self.existing
        missing = self.missing
        timeline = self.timeline
        for i, date in enumerate(existing):
            timeline.append(date)
            next_expected = self.date.next(date)
            next_existing = existing[i + 1] if i + 1 < len(existing) else None
            while next_existing and next_expected < next_existing:
                timeline.append(next_expected)
                if next_expected not in dangling_journals:
                    missing.append(next_expected)
                next_expected = self.date.next(next_expected)
        all = sorted(timeline + dangling_journals)
        stats = self.timeline_stats
        stats["timeline"] = self.date.stats(timeline)
        stats["dangling"] = self.date.stats(dangling_journals)
        stats["total"] = self.date.stats(all)
        self.all.extend(all)

    def get_dangling_journals_outside_range(self, dangling_journals: list[datetime]) -> None:
        """Check for dangling journals that are outside the range of the complete timeline."""
        dangling = self.dangling
        stats = self.timeline_stats["timeline"]
        for link in dangling_journals:
            if link < stats["first"]:
                dangling["past"].append(link)
            elif link > stats["last"]:
                dangling["future"].append(link)
            else:
                dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, Any]:
        """Get a report of the journal processing results."""
        return {
            Output.JOURNALS_ALL.value: self.all,
            Output.JOURNALS_DANGLING.value: self.dangling,
            Output.JOURNALS_EXISTING.value: self.existing,
            Output.JOURNALS_TIMELINE.value: self.timeline,
            Output.JOURNALS_MISSING.value: self.missing,
            Output.JOURNALS_TIMELINE_STATS.value: self.timeline_stats,
        }
