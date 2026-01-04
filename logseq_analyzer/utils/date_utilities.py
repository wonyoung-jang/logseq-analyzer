"""DateUtilities class to handle date-related operations."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

logger = logging.getLogger(__name__)

__all__ = [
    "DATE_ORDINAL_SUFFIXES",
    "DateStat",
    "DateUtilities",
    "Day",
]


class Day(IntEnum):
    """Enum for days of the week."""

    IN_WEEK = 7
    IN_MONTH = 30
    IN_YEAR = 365


class DateStat(StrEnum):
    """Enum for date statistics."""

    FIRST = "first"
    LAST = "last"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"


DATE_ORDINAL_SUFFIXES: frozenset[str] = frozenset({"st", "nd", "rd", "th"})
DATETIME_TOKEN_MAP: dict[str, str] = {
    "yyyy": "%Y",
    "xxxx": "%Y",
    "yy": "%y",
    "xx": "%y",
    "MMMM": "%B",
    "MMM": "%b",
    "MM": "%m",
    "M": "%#m",
    "dd": "%d",
    "d": "%#d",
    "D": "%j",
    "EEEE": "%A",
    "EEE": "%a",
    "EE": "%a",
    "E": "%a",
    "e": "%u",
    "HH": "%H",
    "H": "%H",
    "hh": "%I",
    "h": "%I",
    "mm": "%M",
    "m": "%#M",
    "ss": "%S",
    "s": "%#S",
    "SSS": "%f",
    "a": "%p",
    "A": "%p",
    "Z": "%z",
    "ZZ": "%z",
}

DY = Day
DS = DateStat


class DateUtilities:
    """DateUtilities class to handle date-related operations."""

    @staticmethod
    def next(date_obj: datetime) -> datetime:
        """Return the date of the next day."""
        return date_obj + timedelta(days=1)

    @staticmethod
    def range(stats: dict[str, datetime]) -> dict[str, float | None]:
        """Compute the range between two dates in days, weeks, months, and years."""
        delta = stats[DS.LAST] - stats[DS.FIRST]
        days = delta.days + 1
        return {
            DS.DAYS: days if delta else 0.0,
            DS.WEEKS: round(days / DY.IN_WEEK, 2) if delta else 0.0,
            DS.MONTHS: round(days / DY.IN_MONTH, 2) if delta else 0.0,
            DS.YEARS: round(days / DY.IN_YEAR, 2) if delta else 0.0,
        }

    @staticmethod
    def stats(dates: list[datetime]) -> dict[str, Any]:
        """Get statistics about the timeline."""
        stats = {
            DS.FIRST: min(dates) if dates else datetime.min.replace(tzinfo=None),
            DS.LAST: max(dates) if dates else datetime.min.replace(tzinfo=None),
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
    def journals_to_datetime(keys: Iterable[str], py_page_format: str = "") -> Generator[datetime, Any, None]:
        """Convert journal keys from strings to datetime objects."""
        for key in keys:
            try:
                key_to_parse = key
                for ordinal in DATE_ORDINAL_SUFFIXES:
                    key_to_parse = key_to_parse.replace(ordinal, "")
                yield datetime.strptime(key_to_parse, py_page_format.replace("#", "")).replace(tzinfo=UTC)
            except ValueError:
                pass

    @staticmethod
    def compile_datetime_tokens() -> re.Pattern:
        """Set the regex pattern for date tokens."""
        token_map = DATETIME_TOKEN_MAP
        pattern = "|".join(re.escape(k) for k in sorted(token_map.keys(), key=len, reverse=True))
        return re.compile(pattern)

    @staticmethod
    def cljs_date_to_py(cljs_format: str, token_pattern: re.Pattern) -> str:
        """Convert a Clojure-style date format to a Python-style date format."""
        cljs_format = cljs_format.replace("o", "")
        get_token = DATETIME_TOKEN_MAP.get

        def replace_token(match: re.Match) -> str:
            """Replace a date token with its corresponding Python format."""
            token = match.group(0)
            return get_token(token, token)

        return token_pattern.sub(replace_token, cljs_format)
