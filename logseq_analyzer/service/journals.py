"""Process logseq journals."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import IntEnum
from itertools import chain
from typing import TYPE_CHECKING, TypedDict

from logseq_analyzer.utils.enums import Output, OutputDir

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from logseq_analyzer.domain.index import FileIndex


class Day(IntEnum):
    """Enum for days of the week."""

    IN_WEEK = 7
    IN_MONTH = 30
    IN_YEAR = 365


_DATE_ORDINAL_SUFFIXES = frozenset(("st", "nd", "rd", "th"))


class JournalStat(TypedDict):
    """TypedDict for journal statistics."""

    first: datetime
    last: datetime
    days: int
    weeks: float
    months: float
    years: float


def _get_journal_stats(dates: list[datetime]) -> JournalStat:
    """Get statistics about the timeline."""
    first = min(dates) if dates else datetime.min.replace(tzinfo=UTC)
    last = max(dates) if dates else datetime.min.replace(tzinfo=UTC)
    delta = last - first
    days = delta.days + 1
    return JournalStat(
        first=first,
        last=last,
        days=days,
        weeks=round(days / Day.IN_WEEK, 2),
        months=round(days / Day.IN_MONTH, 2),
        years=round(days / Day.IN_YEAR, 2),
    )


@dataclass(slots=True)
class LogseqJournals:
    """LogseqJournals class to handle journal files and their processing."""

    index: FileIndex
    dangling_links: set[str]
    journal_page_format: str
    all_: list[datetime] = field(default_factory=list)
    existing: list[datetime] = field(default_factory=list)
    missing: list[datetime] = field(default_factory=list)
    timeline: list[datetime] = field(default_factory=list)
    dangling: dict[str, list[datetime]] = field(default_factory=lambda: defaultdict(list))
    stat: dict[str, JournalStat] = field(default_factory=dict)

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
                for ordinal in _DATE_ORDINAL_SUFFIXES:
                    key_to_parse = key_to_parse.replace(ordinal, "")
                yield datetime.strptime(key_to_parse, self.journal_page_format.replace("#", "")).replace(tzinfo=UTC)
            except ValueError:
                pass

    def process(self, dangling_dt: list[datetime]) -> None:
        """Build a complete timeline of journal entries, filling in any missing dates."""
        for i, date in enumerate(self.existing):
            self.timeline.append(date)
            _expected = date + timedelta(days=1)
            _existing = self.existing[i + 1] if i + 1 < len(self.existing) else None
            while _existing and _expected < _existing:
                self.timeline.append(_expected)
                if _expected not in dangling_dt:
                    self.missing.append(_expected)
                _expected = _expected + timedelta(days=1)
        self.all_.extend(sorted(chain(self.timeline, dangling_dt)))
        self.stat = {
            "timeline": _get_journal_stats(self.timeline),
            "dangling": _get_journal_stats(dangling_dt),
            "total": _get_journal_stats(self.all_),
        }
        for link in dangling_dt:
            if link < self.stat["timeline"]["first"]:
                self.dangling["past"].append(link)
            elif link > self.stat["timeline"]["last"]:
                self.dangling["future"].append(link)
            else:
                self.dangling["inside"].append(link)

    @property
    def report(self) -> dict[str, object]:
        """Get a report of the journal processing results."""
        return {
            OutputDir.JOURNALS: {
                Output.JOURNALS_ALL: self.all_,
                Output.JOURNALS_DANGLING: self.dangling,
                Output.JOURNALS_EXISTING: self.existing,
                Output.JOURNALS_TIMELINE: self.timeline,
                Output.JOURNALS_MISSING: self.missing,
                Output.JOURNALS_TIMELINE_STATS: self.stat,
            }
        }
