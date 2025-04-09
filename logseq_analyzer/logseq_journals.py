"""
Process logseq journals.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

from ._global_objects import ANALYZER_CONFIG


class LogseqJournals:
    """
    LogseqJournals class to handle journal files and their processing.
    """

    def __init__(self, graph):
        """
        Initialize the LogseqJournals class.
        """
        self.dangling_links = graph.dangling_links
        self.journal_keys = graph.summary_file_subsets["___is_filetype_journal"]
        self.dangling_journals = []
        self.processed_keys = []
        self.complete_timeline = []
        self.missing_keys = []
        self.timeline_stats = {}

    def extract_journals_from_dangling_links(self):
        """
        Extract and sort journal keys from a set of dangling link strings.
        """
        for link in self.dangling_links:
            try:
                if any(ordinal in link for ordinal in ("st", "nd", "rd", "th")):
                    link = link.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
                date_obj = datetime.strptime(
                    link,
                    ANALYZER_CONFIG.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT").replace("#", ""),
                )
                self.dangling_journals.append(date_obj)
            except ValueError as e:
                logging.debug("Invalid date format for key: %s. Error: %s", link, e)
        self.dangling_journals.sort()

    def process_journals_timelines(self) -> None:
        """
        Process journal keys to build the complete timeline and detect missing entries.
        """
        # Convert journal keys from strings to datetime objects
        self.process_journal_keys_to_datetime()
        self.build_complete_timeline()
        self.timeline_stats["complete_timeline"] = LogseqJournals.get_date_stats(self.complete_timeline)
        self.timeline_stats["dangling_journals"] = LogseqJournals.get_date_stats(self.dangling_journals)
        complete_timeline_first_date = self.timeline_stats["complete_timeline"]["first_date"]
        dangling_journals_first_date = self.timeline_stats["dangling_journals"]["first_date"]
        complete_timeline_last_date = self.timeline_stats["complete_timeline"]["last_date"]
        dangling_journals_last_date = self.timeline_stats["dangling_journals"]["last_date"]
        if complete_timeline_first_date > dangling_journals_first_date:
            self.dangling_journals_past = self.get_dangling_journals_past(complete_timeline_first_date)
        if complete_timeline_last_date < dangling_journals_last_date:
            self.dangling_journals_future = self.get_dangling_journals_future(complete_timeline_last_date)

    def process_journal_keys_to_datetime(self):
        """
        Convert journal keys from strings to datetime objects.
        """
        for key in self.journal_keys:
            try:
                if any(ordinal in key for ordinal in ("st", "nd", "rd", "th")):
                    key = key.replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
                date_obj = datetime.strptime(
                    key,
                    ANALYZER_CONFIG.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT").replace("#", ""),
                )
                self.processed_keys.append(date_obj)
            except ValueError as e:
                logging.warning("Invalid date format for key: %s. Error: %s", key, e)

    def build_complete_timeline(self):
        """
        Build a complete timeline of journal entries, filling in any missing dates.
        """
        # Iterate over the sorted keys to construct a continuous timeline.
        for i in range(len(self.processed_keys) - 1):
            current_date = self.processed_keys[i]
            next_expected_date = LogseqJournals.get_next_day(current_date)
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
                next_expected_date = LogseqJournals.get_next_day(next_expected_date)

        # Add the last journal key if available.
        if self.processed_keys:
            self.complete_timeline.append(self.processed_keys[-1])

    @staticmethod
    def get_next_day(date_obj: datetime) -> datetime:
        """
        Return the date of the next day.
        """
        return date_obj + timedelta(days=1)

    @staticmethod
    def get_date_stats(timeline):
        """
        Get statistics about the timeline.
        """
        if not timeline:
            return {
                "first_date": datetime.min,
                "last_date": datetime.min,
                "days": 0,
                "weeks": 0,
                "months": 0,
                "years": 0,
            }
        first_date = min(timeline)
        last_date = max(timeline)
        days, weeks, months, years = LogseqJournals.get_date_ranges(last_date, first_date)
        journal_stats = {
            "first_date": first_date,
            "last_date": last_date,
            "days": days,
            "weeks": weeks,
            "months": months,
            "years": years,
        }
        return journal_stats

    @staticmethod
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

    def get_dangling_journals_past(self, timeline_start: datetime) -> List[datetime]:
        """
        Get dangling journals that are before the timeline start date.
        """
        dangling_journals_past = []
        for link in self.dangling_journals:
            if link < timeline_start:
                dangling_journals_past.append(link)
        return dangling_journals_past

    def get_dangling_journals_future(self, timeline_end: datetime) -> List[datetime]:
        """
        Get dangling journals that are after the timeline end date.
        """
        dangling_journals_future = []
        for link in self.dangling_journals:
            if link > timeline_end:
                dangling_journals_future.append(link)
        return dangling_journals_future


def set_journal_py_formatting():
    """
    Set the formatting for journal files and pages in Python format.
    """
    journal_page_format = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "JOURNAL_PAGE_TITLE_FORMAT")
    journal_file_format = ANALYZER_CONFIG.get("LOGSEQ_CONFIG", "JOURNAL_FILE_NAME_FORMAT")
    py_file_name_format = ANALYZER_CONFIG.get("LOGSEQ_JOURNALS", "PY_FILE_FORMAT")
    if not py_file_name_format:
        py_file_name_format = convert_cljs_date_to_py(journal_file_format)
        ANALYZER_CONFIG.set("LOGSEQ_JOURNALS", "PY_FILE_FORMAT", py_file_name_format)
    py_page_title_no_ordinal = journal_page_format.replace("o", "")
    py_page_title_format_base = ANALYZER_CONFIG.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT")
    if not py_page_title_format_base:
        py_page_title_format_base = convert_cljs_date_to_py(py_page_title_no_ordinal)
        ANALYZER_CONFIG.set("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT", py_page_title_format_base)


def convert_cljs_date_to_py(cljs_format) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.

    Args:
        cljs_format (str): Clojure-style date format.

    Returns:
        str: Python-style date format.
    """
    cljs_format = cljs_format.replace("o", "")

    def replace_token(match):
        token = match.group(0)
        return ANALYZER_CONFIG.datetime_token_map.get(token, token)

    return ANALYZER_CONFIG.datetime_token_pattern.sub(replace_token, cljs_format)
