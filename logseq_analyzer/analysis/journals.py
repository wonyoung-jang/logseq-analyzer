"""Process logseq journals."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum, StrEnum
from typing import TYPE_CHECKING, Any

from logseq_analyzer.utils.enums import Output

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from logseq_analyzer.analysis.index import FileIndex


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


def date_next(date_obj: datetime) -> datetime:
    """Return the date of the next day."""
    return date_obj + timedelta(days=1)


def date_stats(dates: list[datetime]) -> dict[str, Any]:
    """Get statistics about the timeline."""

    def _range(delta: timedelta) -> dict[str, float | None]:
        """Compute the range between two dates in days, weeks, months, and years."""
        days = delta.days + 1
        return {
            DateStat.DAYS: days if delta else 0.0,
            DateStat.WEEKS: round(days / Day.IN_WEEK, 2) if delta else 0.0,
            DateStat.MONTHS: round(days / Day.IN_MONTH, 2) if delta else 0.0,
            DateStat.YEARS: round(days / Day.IN_YEAR, 2) if delta else 0.0,
        }

    stats: dict[str, Any] = {
        DateStat.FIRST: min(dates) if dates else datetime.min.replace(tzinfo=None),
        DateStat.LAST: max(dates) if dates else datetime.min.replace(tzinfo=None),
    }
    delta = stats[DateStat.LAST] - stats[DateStat.FIRST]
    stats.update(_range(delta))
    return stats


def journals_to_datetime(keys: Iterable[str], py_page_format: str = "") -> Iterator[datetime]:
    """Convert journal keys from strings to datetime objects."""
    for key in keys:
        try:
            key_to_parse = key
            for ordinal in DATE_ORDINAL_SUFFIXES:
                key_to_parse = key_to_parse.replace(ordinal, "")
            yield datetime.strptime(key_to_parse, py_page_format.replace("#", "")).replace(tzinfo=UTC)
        except ValueError:
            pass


@dataclass(slots=True)
class LogseqJournals:
    """LogseqJournals class to handle journal files and their processing."""

    index: FileIndex
    dangling_links: set[str]
    journal_page_format: str
    all_journals: list[datetime] = field(default_factory=list)
    existing: list[datetime] = field(default_factory=list)
    missing: list[datetime] = field(default_factory=list)
    timeline: list[datetime] = field(default_factory=list)
    dangling: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))
    timeline_stats: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize the LogseqJournals class."""
        _dangling_journals = sorted(self._journals_to_datetime(self.dangling_links))
        self.existing.extend(sorted(self._journals_to_datetime(self.index.yield_journals())))
        self.process(_dangling_journals)

    def __len__(self) -> int:
        """Return the number of processed keys."""
        return len(self.timeline)

    def _journals_to_datetime(self, keys: Iterable[str]) -> Iterator[datetime]:
        """Convert journal keys from strings to datetime objects."""
        for key in keys:
            try:
                key_to_parse = key
                for ordinal in DATE_ORDINAL_SUFFIXES:
                    key_to_parse = key_to_parse.replace(ordinal, "")
                yield datetime.strptime(key_to_parse, self.journal_page_format.replace("#", "")).replace(tzinfo=UTC)
            except ValueError:
                pass

    def process(self, dangling_journals: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        for i, date in enumerate(self.existing):
            self.timeline.append(date)
            next_expected = date_next(date)
            next_existing = self.existing[i + 1] if i + 1 < len(self.existing) else None
            while next_existing and next_expected < next_existing:
                self.timeline.append(next_expected)
                if next_expected not in dangling_journals:
                    self.missing.append(next_expected)
                next_expected = date_next(next_expected)
        self.all_journals.extend(sorted(self.timeline + dangling_journals))
        self.timeline_stats = {
            "timeline": date_stats(self.timeline),
            "dangling": date_stats(dangling_journals),
            "total": date_stats(self.all_journals),
        }
        for link in dangling_journals:
            if link < self.timeline_stats["timeline"]["first"]:
                self.dangling["past"].append(link)
            elif link > self.timeline_stats["timeline"]["last"]:
                self.dangling["future"].append(link)
            else:
                self.dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, Any]:
        """Get a report of the journal processing results."""
        return {
            Output.JOURNALS_ALL: self.all_journals,
            Output.JOURNALS_DANGLING: self.dangling,
            Output.JOURNALS_EXISTING: self.existing,
            Output.JOURNALS_TIMELINE: self.timeline,
            Output.JOURNALS_MISSING: self.missing,
            Output.JOURNALS_TIMELINE_STATS: self.timeline_stats,
        }
