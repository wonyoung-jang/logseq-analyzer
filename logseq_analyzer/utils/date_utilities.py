"""
DateUtilities class to handle date-related operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Generator

logger = logging.getLogger(__name__)

__all__ = [
    "DateUtilities",
]


class DateUtilities:
    """DateUtilities class to handle date-related operations."""

    _DATE_ORDINAL_SUFFIXES: frozenset[str] = frozenset({"st", "nd", "rd", "th"})

    @staticmethod
    def next(date_obj: datetime) -> datetime:
        """Return the date of the next day."""
        return date_obj + timedelta(days=1)

    @staticmethod
    def range(date_stats: dict[str, datetime | None]) -> dict[str, float | None]:
        """Compute the range between two dates in days, weeks, months, and years."""
        delta = date_stats["last"] - date_stats["first"]
        days = delta.days + 1
        return {
            "days": days if delta else 0.0,
            "weeks": round(days / 7, 2) if delta else 0.0,
            "months": round(days / 30, 2) if delta else 0.0,
            "years": round(days / 365, 2) if delta else 0.0,
        }

    @staticmethod
    def stats(timeline: list[datetime]) -> dict[str, Any]:
        """Get statistics about the timeline."""
        date_stats = {
            "first": min(timeline) if timeline else datetime.min,
            "last": max(timeline) if timeline else datetime.min,
        }
        date_stats.update(DateUtilities.range(date_stats))
        return date_stats

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
        _ordinal_suffixes = DateUtilities._DATE_ORDINAL_SUFFIXES
        for key in keys:
            try:
                for ordinal in _ordinal_suffixes:
                    key = key.replace(ordinal, "")
                yield datetime.strptime(key, py_page_format.replace("#", ""))
            except ValueError:
                pass
