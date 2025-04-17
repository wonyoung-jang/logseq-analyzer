"""
Process logseq journals.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

from ..config.datetime_tokens import LogseqJournalFormats
from ..utils.helpers import singleton
from .summary_files import LogseqFileSummarizer
from .graph import LogseqGraph
from ..utils.enums import SummaryFiles


@singleton
class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    def __init__(self):
        """
        Initialize the LogseqJournals class.
        """
        graph = LogseqGraph()
        summary_files = LogseqFileSummarizer()
        self.dangling_links = graph.dangling_links
        self.journal_keys = summary_files.subsets.get(SummaryFiles.FILETYPE_JOURNAL.value, [])
        self.dangling_journals = []
        self.processed_keys = []
        self.complete_timeline = []
        self.missing_keys = []
        self.timeline_stats = {}
        self.dangling_journals_past = []
        self.dangling_journals_future = []

    def process_journals_timelines(self) -> None:
        """
        Process journal keys to build the complete timeline and detect missing entries.
        """
        py_page_fmt = LogseqJournalFormats()
        py_page_base_format = py_page_fmt.py_page_format

        for dateobj in self.process_journal_keys_to_datetime(self.dangling_links, py_page_base_format):
            self.dangling_journals.append(dateobj)
        self.dangling_journals.sort()

        for dateobj in self.process_journal_keys_to_datetime(self.journal_keys, py_page_base_format):
            self.processed_keys.append(dateobj)
        self.processed_keys.sort()

        self.build_complete_timeline()
        self.timeline_stats["complete_timeline"] = get_date_stats(self.complete_timeline)
        self.timeline_stats["dangling_journals"] = get_date_stats(self.dangling_journals)
        self.get_dangling_journals_outside_range()

    def process_journal_keys_to_datetime(self, list_of_keys: List[str], py_page_base_format: str = None):
        """
        Convert journal keys from strings to datetime objects.
        """
        for key in list_of_keys:
            try:
                if any(ordinal in key for ordinal in ("st", "nd", "rd", "th")):
                    key = key.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
                yield datetime.strptime(key, py_page_base_format.replace("#", ""))
            except ValueError as e:
                logging.warning("Invalid date format for key: %s. Error: %s", key, e)

    def build_complete_timeline(self):
        """
        Build a complete timeline of journal entries, filling in any missing dates.
        """
        # Iterate over the sorted keys to construct a continuous timeline.
        for i in range(len(self.processed_keys) - 1):
            current_date = self.processed_keys[i]
            next_expected_date = get_next_day(current_date)
            next_actual_date = self.processed_keys[i + 1]

            # Always include the current date
            self.complete_timeline.append(current_date)

            # If there is a gap, fill in missing dates
            while next_expected_date < next_actual_date:
                self.complete_timeline.append(next_expected_date)
                if next_expected_date in self.dangling_journals:
                    # Remove matching dangling link if found (assuming dangling_links are datetime objects)
                    self.dangling_journals.remove(next_expected_date)
                else:
                    self.missing_keys.append(next_expected_date)
                next_expected_date = get_next_day(next_expected_date)

        # Add the last journal key if available.
        if self.processed_keys:
            self.complete_timeline.append(self.processed_keys[-1])

    def get_dangling_journals_outside_range(self):
        """
        Check for dangling journals that are outside the range of the complete timeline.
        """
        for link in self.dangling_journals:
            if link < self.timeline_stats["complete_timeline"]["first_date"]:
                self.dangling_journals_past.append(link)
                continue
            if link > self.timeline_stats["complete_timeline"]["last_date"]:
                self.dangling_journals_future.append(link)
                continue


def get_next_day(date_obj: datetime) -> datetime:
    """
    Return the date of the next day.
    """
    return date_obj + timedelta(days=1)


def get_date_stats(timeline):
    """
    Get statistics about the timeline.
    """
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
    days, weeks, months, years = get_date_ranges(date_stats["last_date"], date_stats["first_date"])
    date_stats["days"] = days
    date_stats["weeks"] = weeks
    date_stats["months"] = months
    date_stats["years"] = years
    return date_stats


def get_date_ranges(
    most_recent_date: Optional[datetime], least_recent_date: Optional[datetime]
) -> Tuple[Optional[int], Optional[float], Optional[float], Optional[float]]:
    """
    Compute the range between two dates in days, weeks, months, and years.
    """
    if not most_recent_date or not least_recent_date:
        return None, None, None, None

    delta = most_recent_date - least_recent_date
    days = delta.days + 1
    weeks = round(days / 7, 2)
    months = round(days / 30, 2)
    years = round(days / 365, 2)
    return days, weeks, months, years
