"""
Process logseq journals.
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Generator, TYPE_CHECKING

from ..analysis.index import get_attribute_list
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
    def range(
        most_recent_date: datetime | None, least_recent_date: datetime | None
    ) -> tuple[int | None, float | None, float | None, float | None]:
        """Compute the range between two dates in days, weeks, months, and years."""
        if not most_recent_date or not least_recent_date:
            return None, None, None, None

        delta = most_recent_date - least_recent_date
        days = delta.days + 1
        weeks = round(days / 7, 2)
        months = round(days / 30, 2)
        years = round(days / 365, 2)
        return days, weeks, months, years

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
        days, weeks, months, years = DateUtilities.range(date_stats["last_date"], date_stats["first_date"])
        date_stats["days"] = days
        date_stats["weeks"] = weeks
        date_stats["months"] = months
        date_stats["years"] = years
        return date_stats


@singleton
class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    __slots__ = (
        "dangling_journals",
        "processed_keys",
        "complete_timeline",
        "missing_keys",
        "timeline_stats",
        "dangling_journals_dict",
        "date",
    )

    def __init__(self, date_utilities: DateUtilities = DateUtilities) -> None:
        """Initialize the LogseqJournals class."""
        self.dangling_journals: list[datetime] = []
        self.processed_keys: list[datetime] = []
        self.complete_timeline: list[datetime] = []
        self.missing_keys: list[datetime] = []
        self.timeline_stats: dict[str, Any] = {}
        self.dangling_journals_dict: defaultdict[str, list[datetime]] = defaultdict(list)
        self.date: DateUtilities = date_utilities

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
        dangling_journals = list(self.process_journal_keys_to_datetime(dangling_links, py_page_base_format))
        self.dangling_journals = sorted(dangling_journals)
        journal_criteria = {"file_type": "journal"}
        journal_keys = index.filter_files(**journal_criteria)
        journal_keys = get_attribute_list(journal_keys, "name")
        processed_keys = list(self.process_journal_keys_to_datetime(journal_keys, py_page_base_format))
        self.processed_keys = sorted(processed_keys)

        self.build_complete_timeline()
        self.timeline_stats["complete_timeline"] = self.date.stats(self.complete_timeline)
        self.timeline_stats["dangling_journals"] = self.date.stats(self.dangling_journals)
        self.get_dangling_journals_outside_range()

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

    def build_complete_timeline(self) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        processed_keys = self.processed_keys
        dangling_journals = self.dangling_journals
        missing_keys = self.missing_keys
        complete_timeline = self.complete_timeline
        for i in range(len(processed_keys) - 1):
            current_date = processed_keys[i]
            complete_timeline.append(current_date)
            next_expected_date = self.date.next(current_date)
            next_actual_date = processed_keys[i + 1]
            while next_expected_date < next_actual_date:
                complete_timeline.append(next_expected_date)
                if next_expected_date in dangling_journals:
                    dangling_journals.remove(next_expected_date)
                else:
                    missing_keys.append(next_expected_date)
                next_expected_date = self.date.next(next_expected_date)

        if processed_keys:
            complete_timeline.append(processed_keys[-1])

    def get_dangling_journals_outside_range(self) -> None:
        """Check for dangling journals that are outside the range of the complete timeline."""
        dangling_journals = self.dangling_journals
        timeline_stats = self.timeline_stats["complete_timeline"]
        dangling_journals_dict = self.dangling_journals_dict
        for link in dangling_journals:
            if link < timeline_stats["first_date"]:
                dangling_journals_dict["past"].append(link)
            elif link > timeline_stats["last_date"]:
                dangling_journals_dict["future"].append(link)
