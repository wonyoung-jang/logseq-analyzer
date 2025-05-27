"""
DateUtilities class to handle date-related operations.
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Generator

from ..utils.helpers import singleton

__all__ = [
    "DateUtilities",
    "DATE_ORDINAL_SUFFIXES",
]

DATE_ORDINAL_SUFFIXES: tuple[str] = ("st", "nd", "rd", "th")


@singleton
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
        if not (delta := date_stats["last"] - date_stats["first"]):
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
            "first": datetime.min,
            "last": datetime.min,
            "days": 0,
            "weeks": 0,
            "months": 0,
            "years": 0,
        }
        if not timeline:
            return date_stats

        date_stats["first"] = min(timeline)
        date_stats["last"] = max(timeline)
        date_stats.update(DateUtilities.range(date_stats))
        return date_stats

    @staticmethod
    def append_ordinal_to_day(day: str) -> str:
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        day_number = int(day)
        if 11 <= day_number <= 13:
            return day + "th"
        return day + {1: "st", 2: "nd", 3: "rd"}.get(day_number % 10, "th")

    @staticmethod
    def journals_to_datetime(keys: list[str], py_page_format: str = "") -> Generator[datetime, Any, None]:
        """Convert journal keys from strings to datetime objects."""
        for key in keys:
            try:
                for ordinal in DATE_ORDINAL_SUFFIXES:
                    key = key.replace(ordinal, "")
                yield datetime.strptime(key, py_page_format.replace("#", ""))
            except ValueError as e:
                logging.warning("Invalid date format for key: %s. Error: %s", key, e)
