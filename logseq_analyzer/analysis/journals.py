"""
Process logseq journals.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, TYPE_CHECKING

from ..analysis.index import get_attribute_list
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
        "complete_timeline",
        "dangling",
        "date",
        "missing",
        "processed",
        "timeline_stats",
    )

    def __init__(self, date_utilities: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqJournals class."""
        self.complete_timeline: list[datetime] = []
        self.dangling: defaultdict[str, list[datetime]] = defaultdict(list)
        self.date: DateUtilities = date_utilities
        self.missing: list[datetime] = []
        self.processed: list[datetime] = []
        self.timeline_stats: dict[str, Any] = {}

    def __repr__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqJournals class."""
        return f"{self.__class__.__qualname__}"

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.complete_timeline)

    def process_journals_timelines(
        self, index: "FileIndex", dangling_links: list[str], py_page_base_format: str
    ) -> None:
        """Process journal keys to build the complete timeline and detect missing entries."""
        dangling_journals = sorted(self.date.journals_to_datetime(dangling_links, py_page_base_format))
        journal_criteria = {"file_type": "journal"}
        journal_keys = index.filter_files(**journal_criteria)
        journal_keys = get_attribute_list(journal_keys, "name")
        self.processed = sorted(self.date.journals_to_datetime(journal_keys, py_page_base_format))
        self.build_complete_timeline(dangling_journals)
        self.get_dangling_journals_outside_range(dangling_journals)

    def build_complete_timeline(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        processed = self.processed
        missing = self.missing
        complete_timeline = self.complete_timeline
        for i in range(len(processed) - 1):
            current_date = processed[i]
            complete_timeline.append(current_date)
            next_expected_date = self.date.next(current_date)
            next_actual_date = processed[i + 1]
            while next_expected_date < next_actual_date:
                complete_timeline.append(next_expected_date)
                if next_expected_date in dangling_journals:
                    dangling_journals.remove(next_expected_date)
                else:
                    missing.append(next_expected_date)
                next_expected_date = self.date.next(next_expected_date)

        if processed:
            complete_timeline.append(processed[-1])

        self.timeline_stats["complete_timeline"] = self.date.stats(complete_timeline)
        self.timeline_stats["dangling_journals"] = self.date.stats(dangling_journals)

    def get_dangling_journals_outside_range(self, dangling_journals: list[datetime]) -> None:
        """Check for dangling journals that are outside the range of the complete timeline."""
        timeline_stats = self.timeline_stats["complete_timeline"]
        dangling = self.dangling
        for link in dangling_journals:
            if link < timeline_stats["first_date"]:
                dangling["past"].append(link)
            elif link > timeline_stats["last_date"]:
                dangling["future"].append(link)

    @property
    def report(self) -> dict[str, Any]:
        """Get a report of the journal processing results."""
        return {
            Output.DANGLING_JOURNALS.value: self.dangling,
            Output.PROCESSED_JOURNALS.value: self.processed,
            Output.COMPLETE_TIMELINE.value: self.complete_timeline,
            Output.MISSING_JOURNALS.value: self.missing,
            Output.TIMELINE_STATS.value: self.timeline_stats,
        }
