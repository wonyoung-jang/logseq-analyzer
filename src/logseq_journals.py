"""
Process logseq journals.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union

from .reporting import write_output
from .config_loader import get_config


CONFIG = get_config()
OUTPUT_DIR = CONFIG.get("ANALYZER", "OUTPUT_DIR")
JOURNAL_DIR = CONFIG.get("OUTPUT_DIRS", "LOGSEQ_JOURNALS")


def process_logseq_journal_key(key: str) -> str:
    """
    Process the journal key to create a page title.

    Args:
        key (str): The key name (filename stem).

    Returns:
        str: Processed page title.
    """
    journal_page_format = CONFIG.get("LOGSEQ_CONFIG", "JOURNAL_PAGE_TITLE_FORMAT")
    journal_file_format = CONFIG.get("LOGSEQ_CONFIG", "JOURNAL_FILE_NAME_FORMAT")

    py_file_name_format = CONFIG.get("LOGSEQ_JOURNALS", "PY_FILE_FORMAT")
    if not py_file_name_format:
        py_file_name_format = convert_cljs_date_to_py(journal_file_format)
        CONFIG.set("LOGSEQ_JOURNALS", "PY_FILE_FORMAT", py_file_name_format)

    py_page_title_no_ordinal = journal_page_format.replace("o", "")

    py_page_title_format_base = CONFIG.get("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT")
    if not py_page_title_format_base:
        py_page_title_format_base = convert_cljs_date_to_py(py_page_title_no_ordinal)
        CONFIG.set("LOGSEQ_JOURNALS", "PY_PAGE_BASE_FORMAT", py_page_title_format_base)

    try:
        date_object = datetime.strptime(key, py_file_name_format)
        page_title_base = date_object.strftime(py_page_title_format_base).lower()
        if "o" in journal_page_format:
            day_number = date_object.day
            day_with_ordinal = add_ordinal_suffix_to_day_of_month(day_number)
            page_title = page_title_base.replace(f"{day_number}", day_with_ordinal)
        else:
            page_title = page_title_base
        page_title = page_title.replace("'", "")
        return page_title
    except ValueError as e:
        logging.warning("Failed to parse date from key '%s', format `%s`: %s", key, py_file_name_format, e)
        return key


def convert_cljs_date_to_py(cljs_format: str) -> str:
    """
    Convert a Clojure-style date format to a Python-style date format.

    Args:
        cljs_format (str): Clojure-style date format.

    Returns:
        str: Python-style date format.
    """
    cljs_format = cljs_format.replace("o", "")
    datetime_token_map = CONFIG.get_datetime_token_map()
    datetime_token_pattern = CONFIG.get_datetime_token_pattern()

    def replace_token(match):
        token = match.group(0)
        return datetime_token_map.get(token, token)

    py_format = datetime_token_pattern.sub(replace_token, cljs_format)
    return py_format


def add_ordinal_suffix_to_day_of_month(day):
    """Get day of month with ordinal suffix (1st, 2nd, 3rd, 4th, etc.)."""
    if 11 <= day <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return str(day) + suffix


def process_journals_timelines(journal_keys: List[str], dangling_journals: List[Union[str, datetime]]) -> None:
    """
    Process journal keys to build the complete timeline and detect missing entries.

    Args:
        journal_keys (List[str]): List of journal key strings.
        dangling_journals (List[Union[str, datetime]]): List of dangling link keys (either strings or datetime objects).
    """
    # Convert journal keys from strings to datetime objects
    processed_keys = process_journal_keys_to_datetime(journal_keys)
    complete_timeline, missing_keys = build_complete_timeline(dangling_journals, processed_keys)

    # Write out results to files.
    write_output(OUTPUT_DIR, "complete_timeline", complete_timeline, JOURNAL_DIR)
    write_output(OUTPUT_DIR, "processed_keys", processed_keys, JOURNAL_DIR)
    write_output(OUTPUT_DIR, "missing_keys", missing_keys, JOURNAL_DIR)
    write_output(OUTPUT_DIR, "dangling_journals", dangling_journals, JOURNAL_DIR)

    timeline_stats = {}
    timeline_stats["complete_timeline"] = get_date_stats(complete_timeline)
    timeline_stats["dangling_journals"] = get_date_stats(dangling_journals)
    write_output(OUTPUT_DIR, "timeline_stats", timeline_stats, JOURNAL_DIR)

    if timeline_stats["complete_timeline"]["first_date"] > timeline_stats["dangling_journals"]["first_date"]:
        dangling_journals_past = get_dangling_journals_past(
            dangling_journals, timeline_stats["complete_timeline"]["first_date"]
        )
        write_output(OUTPUT_DIR, "dangling_journals_past", dangling_journals_past, JOURNAL_DIR)

    if timeline_stats["complete_timeline"]["last_date"] < timeline_stats["dangling_journals"]["last_date"]:
        dangling_journals_future = get_dangling_journals_future(
            dangling_journals, timeline_stats["complete_timeline"]["last_date"]
        )
        write_output(OUTPUT_DIR, "dangling_journals_future", dangling_journals_future, JOURNAL_DIR)


def process_journal_keys_to_datetime(journal_keys: List[str]) -> List[datetime]:
    """
    Convert journal keys from strings to datetime objects.

    Args:
        journal_keys (List[str]): List of journal key strings.

    Returns:
        List[datetime]: List of datetime objects.
    """
    processed_keys = []
    for key in journal_keys:
        try:
            date_obj = datetime.strptime(key, "%Y-%m-%d %A")
            processed_keys.append(date_obj)
        except ValueError as e:
            logging.warning("Invalid date format for key: %s. Error: %s", key, e)
    return processed_keys


def build_complete_timeline(dangling_journals, processed_keys):
    """
    Build a complete timeline of journal entries, filling in any missing dates.
    """
    complete_timeline = []
    missing_keys = []

    # Iterate over the sorted keys to construct a continuous timeline.
    for i in range(len(processed_keys) - 1):
        current_date = processed_keys[i]
        next_expected_date = get_next_day(current_date)
        next_actual_date = processed_keys[i + 1]

        # Always include the current date
        complete_timeline.append(current_date)

        # If there is a gap, fill in missing dates
        while next_expected_date < next_actual_date:
            complete_timeline.append(next_expected_date)
            if next_expected_date in dangling_journals:
                # Remove matching dangling link if found (assuming dangling_links are datetime objects)
                dangling_journals.remove(next_expected_date)
            else:
                missing_keys.append(next_expected_date)
            next_expected_date = get_next_day(next_expected_date)

    # Add the last journal key if available.
    if processed_keys:
        complete_timeline.append(processed_keys[-1])
    return complete_timeline, missing_keys


def get_date_stats(timeline):
    """
    Get statistics about the timeline.
    """
    first_date = min(timeline)
    last_date = max(timeline)
    days, weeks, months, years = get_date_ranges(last_date, first_date)
    journal_stats = {
        "first_date": first_date,
        "last_date": last_date,
        "days": days,
        "weeks": weeks,
        "months": months,
        "years": years,
    }
    return journal_stats


def get_dangling_journals_past(dangling_links: List[str], timeline_start: datetime) -> List[datetime]:
    """
    Get dangling journals that are before the timeline start date.
    """
    dangling_journals_past = []
    for link in dangling_links:
        if link < timeline_start:
            dangling_journals_past.append(link)
    return dangling_journals_past


def get_dangling_journals_future(dangling_links: List[str], timeline_end: datetime) -> List[datetime]:
    """
    Get dangling journals that are after the timeline end date.
    """
    dangling_journals_future = []
    for link in dangling_links:
        if link > timeline_end:
            dangling_journals_future.append(link)
    return dangling_journals_future


def extract_journals_from_dangling_links(dangling_links: List[str]) -> List[datetime]:
    """
    Extract and sort journal keys from a list of dangling link strings.

    Only keys that match the journal format "%Y-%m-%d %A" are considered.

    Args:
        dangling_links (List[str]): List of dangling link strings.

    Returns:
        List[datetime]: Sorted list of journal datetime objects.
    """
    journal_keys = []
    for link in dangling_links:
        try:
            date_obj = datetime.strptime(link, "%Y-%m-%d %A")
            journal_keys.append(date_obj)
        except ValueError:
            continue
    journal_keys.sort()
    return journal_keys


def get_date_ranges(
    most_recent_date: Optional[datetime], least_recent_date: Optional[datetime]
) -> Tuple[Optional[int], Optional[float], Optional[float], Optional[float]]:
    """
    Compute the range between two dates in days, weeks, months, and years.

    Args:
        most_recent_date (Optional[datetime]): The latest date.
        least_recent_date (Optional[datetime]): The earliest date.

    Returns:
        Tuple[Optional[int], Optional[float], Optional[float], Optional[float]]:
            The date range in days, weeks, months, and years.
    """
    if not most_recent_date or not least_recent_date:
        return None, None, None, None

    delta = most_recent_date - least_recent_date
    days = delta.days + 1
    weeks = round(days / 7, 2)
    months = round(days / 30, 2)
    years = round(days / 365, 2)
    return days, weeks, months, years


def get_next_day(date_obj: datetime) -> datetime:
    """
    Return the date of the next day.

    Args:
        date_obj (datetime): The current date.

    Returns:
        datetime: The next day's date.
    """
    return date_obj + timedelta(days=1)


def get_most_recent_date(dates) -> Optional[datetime]:
    """
    Return the most recent (maximum) date from a list.

    Args:
        dates (List[datetime]): List of datetime objects.

    Returns:
        Optional[datetime]: The most recent date or None if the list is empty.
    """
    return max(dates) if dates else None


def get_least_recent_date(dates) -> Optional[datetime]:
    """
    Return the least recent (minimum) date from a list.

    Args:
        dates (List[datetime]): List of datetime objects.

    Returns:
        Optional[datetime]: The least recent date or None if the list is empty.
    """
    return min(dates) if dates else None
