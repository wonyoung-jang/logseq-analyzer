"""
DateUtilities class to handle date-related operations.
"""

from datetime import datetime, timedelta
from typing import Any

from ..utils.helpers import singleton

__all__ = [
    "DateUtilities",
]


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

    @staticmethod
    def add_ordinal_suffix_to_day_of_month(day: str) -> str:
        """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
        day_number = int(day)
        if 11 <= day_number <= 13:
            return day + "th"
        return day + {1: "st", 2: "nd", 3: "rd"}.get(day_number % 10, "th")
