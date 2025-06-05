"""
DateUtilities class to handle date-related operations.
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Generator

logger = logging.getLogger(__name__)

__all__ = [
    "DateUtilities",
    "Day",
    "DateStat",
    "DATE_ORDINAL_SUFFIXES",
]


class Day(Enum):
    """Enum for days of the week."""

    IN_WEEK = 7
    IN_MONTH = 30
    IN_YEAR = 365


class DateStat(Enum):
    """Enum for date statistics."""

    FIRST = "first"
    LAST = "last"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


DATE_ORDINAL_SUFFIXES: frozenset[str] = frozenset({"st", "nd", "rd", "th"})

DY = Day
DS = DateStat


class DateUtilities:
    """DateUtilities class to handle date-related operations."""

    @staticmethod
    def next(date_obj: datetime) -> datetime:
        """Return the date of the next day."""
        return date_obj + timedelta(days=1)

    @staticmethod
    def range(stats: dict[str, datetime | None]) -> dict[str, float | None]:
        """Compute the range between two dates in days, weeks, months, and years."""
        delta = stats[DS.LAST.value] - stats[DS.FIRST.value]
        days = delta.days + 1
        return {
            DS.DAYS.value: days if delta else 0.0,
            DS.WEEKS.value: round(days / DY.IN_WEEK.value, 2) if delta else 0.0,
            DS.MONTHS.value: round(days / DY.IN_MONTH.value, 2) if delta else 0.0,
            DS.YEARS.value: round(days / DY.IN_YEAR.value, 2) if delta else 0.0,
        }

    @staticmethod
    def stats(dates: list[datetime]) -> dict[str, Any]:
        """Get statistics about the timeline."""
        stats = {
            DS.FIRST.value: min(dates) if dates else datetime.min,
            DS.LAST.value: max(dates) if dates else datetime.min,
        }
        stats.update(DateUtilities.range(stats))
        return stats

    @staticmethod
    def append_ordinal_to_day(day: str) -> str:
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        day_as_int = int(day)
        if 11 <= day_as_int <= 13:
            return day + "th"
        return day + {1: "st", 2: "nd", 3: "rd"}.get(day_as_int % 10, "th")

    @staticmethod
    def journals_to_datetime(keys: list[str], py_page_format: str = "") -> Generator[datetime, Any, None]:
        """Convert journal keys from strings to datetime objects."""
        for key in keys:
            try:
                for ordinal in DATE_ORDINAL_SUFFIXES:
                    key = key.replace(ordinal, "")
                yield datetime.strptime(key, py_page_format.replace("#", ""))
            except ValueError:
                pass
