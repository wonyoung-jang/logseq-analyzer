"""
Process logseq journals.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

from ..analysis.index import FileIndex
from ..utils.date_utilities import DateUtilities
from ..utils.enums import FileTypes, Output

__all__ = [
    "LogseqJournals",
]


class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    __slots__ = (
        "all_journals",
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
        self.all_journals: list[datetime] = []
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

    def process(self, index: FileIndex, dangling_links: list[str], journal_file: str = FileTypes.JOURNAL.value) -> None:
        """Process journal keys to build the complete timeline and detect missing entries."""
        page_format = LogseqJournals.journal_page_format
        dangling = sorted(self.date.journals_to_datetime(dangling_links, page_format))
        journal_keys = (f.path.name for f in index if f.path.file_type == journal_file)
        journals = sorted(journal_keys)
        self.existing.extend(sorted(self.date.journals_to_datetime(journals, page_format)))
        self.build_complete_timeline(dangling)
        self.get_dangling_journals_outside_range(dangling)

    def build_complete_timeline(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        existing = self.existing
        timeline = self.timeline
        append_missing = self.missing.append
        append_timeline = timeline.append
        get_stats = self.date.stats
        next_date = self.date.next
        for i, date in enumerate(existing):
            append_timeline(date)
            next_expected = next_date(date)
            next_existing = existing[i + 1] if i + 1 < len(existing) else None
            while next_existing and next_expected < next_existing:
                append_timeline(next_expected)
                if next_expected not in dangling_journals:
                    append_missing(next_expected)
                next_expected = next_date(next_expected)
        all_journals = sorted(timeline + dangling_journals)
        self.timeline_stats = {
            "timeline": get_stats(timeline),
            "dangling": get_stats(dangling_journals),
            "total": get_stats(all_journals),
        }
        self.all_journals.extend(all_journals)

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
            Output.JOURNALS_ALL.value: self.all_journals,
            Output.JOURNALS_DANGLING.value: self.dangling,
            Output.JOURNALS_EXISTING.value: self.existing,
            Output.JOURNALS_TIMELINE.value: self.timeline,
            Output.JOURNALS_MISSING.value: self.missing,
            Output.JOURNALS_TIMELINE_STATS.value: self.timeline_stats,
        }
