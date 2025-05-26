"""
Process logseq journals.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Generator, TYPE_CHECKING

from ..analysis.index import get_attribute_list
from ..utils.enums import Output
from ..utils.helpers import singleton

if TYPE_CHECKING:
    from ..analysis.index import FileIndex


__all__ = [
    "LogseqJournals",
    "DateUtilities",
]


class DateUtilities:
    """DateUtilities class to handle date-related operations."""

    @staticmethod
    def next(date_obj: datetime) -> datetime:
        """Return the date of the next day."""
        return date_obj + timedelta(days=1)

    @staticmethod
    def range(date_stats: dict[str, datetime | None]) -> dict[str, float | None]:
        """Compute the range between two dates in days, weeks, months, and years."""
        date_range = {
            "days": None,
            "weeks": None,
            "months": None,
            "years": None,
        }
        if not (delta := date_stats["last_date"] - date_stats["first_date"]):
            return date_range
        days = delta.days + 1
        date_range["days"] = days
        date_range["weeks"] = round(days / 7, 2)
        date_range["months"] = round(days / 30, 2)
        date_range["years"] = round(days / 365, 2)
        return date_range

    @staticmethod
    def stats(timeline: list[datetime]) -> dict[str, Any]:
        """Get statistics about the timeline."""
        date_stats = {
            "first_date": datetime.min,
            "last_date": datetime.min,
            "days": 0,
            "weeks": 0,
            "months": 0,
            "years": 0,
        }
        if not timeline:
            return date_stats

        date_stats["first_date"] = min(timeline)
        date_stats["last_date"] = max(timeline)
        date_stats.update(DateUtilities.range(date_stats))
        return date_stats


@singleton
class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    __slots__ = (
        "dangling",
        "processed",
        "complete_timeline",
        "missing",
        "timeline_stats",
        "date",
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
        dangling_journals = sorted(self.process_journal_keys_to_datetime(dangling_links, py_page_base_format))
        journal_criteria = {"file_type": "journal"}
        journal_keys = index.filter_files(**journal_criteria)
        journal_keys = get_attribute_list(journal_keys, "name")
        processed = sorted(self.process_journal_keys_to_datetime(journal_keys, py_page_base_format))
        self.processed = processed
        self.build_complete_timeline(dangling_journals)
        self.get_dangling_journals_outside_range(dangling_journals)

    @staticmethod
    def process_journal_keys_to_datetime(
        list_of_keys: list[str], py_page_base_format: str = ""
    ) -> Generator[datetime, Any, None]:
        """Convert journal keys from strings to datetime objects."""
        for key in list_of_keys:
            try:
                for ordinal in ("st", "nd", "rd", "th"):
                    key = key.replace(ordinal, "")
                yield datetime.strptime(key, py_page_base_format.replace("#", ""))
            except ValueError as e:
                logging.warning("Invalid date format for key: %s. Error: %s", key, e)

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
