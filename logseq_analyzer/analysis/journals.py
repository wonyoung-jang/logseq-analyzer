"""
Process logseq journals.
"""

from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ..utils.date_utilities import DateUtilities
from ..utils.enums import Output
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
        "dangling",
        "date",
        "existing",
        "missing",
        "timeline_stats",
        "timeline",
    )

    def __init__(self, date_utilities: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqJournals class."""
        self.dangling: defaultdict[str, list[datetime]] = defaultdict(list)
        self.date: DateUtilities = date_utilities
        self.existing: list[datetime] = []
        self.missing: list[datetime] = []
        self.timeline_stats: dict[str, Any] = {}
        self.timeline: list[datetime] = []

    def __repr__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}"

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.timeline)

    def process_journals_timelines(
        self, index: "FileIndex", dangling_links: list[str], py_page_base_format: str
    ) -> None:
        """Process journal keys to build the complete timeline and detect missing entries."""
        dangling_journals = sorted(self.date.journals_to_datetime(dangling_links, py_page_base_format))
        journal_keys = index.filter_files(file_type="journal")
        journal_keys = sorted((file.path.name for file in journal_keys))
        self.existing = sorted(self.date.journals_to_datetime(journal_keys, py_page_base_format))
        self.build_complete_timeline(dangling_journals)
        self.get_dangling_journals_outside_range(dangling_journals)

    def build_complete_timeline(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        existing = self.existing
        missing = self.missing
        timeline = self.timeline
        timeline_stats = self.timeline_stats
        for i, date in enumerate(existing):
            timeline.append(date)
            next_expected = self.date.next(date)
            next_existing = existing[i + 1] if i + 1 < len(existing) else None
            while next_existing and next_expected < next_existing:
                timeline.append(next_expected)
                if next_expected not in dangling_journals:
                    missing.append(next_expected)
                next_expected = self.date.next(next_expected)
        total_timeline = sorted(timeline + dangling_journals)
        timeline_stats["timeline"] = self.date.stats(timeline)
        timeline_stats["dangling"] = self.date.stats(dangling_journals)
        timeline_stats["total"] = self.date.stats(total_timeline)

    def get_dangling_journals_outside_range(self, dangling_journals: list[datetime]) -> None:
        """Check for dangling journals that are outside the range of the complete timeline."""
        timeline_stats = self.timeline_stats["timeline"]
        dangling = self.dangling
        for link in dangling_journals:
            if link < timeline_stats["first"]:
                dangling["past"].append(link)
            elif link > timeline_stats["last"]:
                dangling["future"].append(link)
            else:
                dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, Any]:
        """Get a report of the journal processing results."""
        return {
            Output.JOURNALS_DANGLING.value: self.dangling,
            Output.JOURNALS_EXISTING.value: self.existing,
            Output.JOURNALS_TIMELINE.value: self.timeline,
            Output.JOURNALS_MISSING.value: self.missing,
            Output.JOURNALS_TIMELINE_STATS.value: self.timeline_stats,
        }
