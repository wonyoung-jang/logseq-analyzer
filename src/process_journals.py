"""
Process logseq journals.

Questions:
- What is the journal timeline implied by the files in the journal folder?
- What journals are missing?
- What journals are dangling links?
- What is the range of the journal timeline?
- What is the range of the journal timeline in days, weeks, months, and years?
- What is the first and last journal key in the timeline?
- What dangling links are journal formatted, but not within the timeline?
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union


def process_journals_timelines(journal_keys: List[str], dangling_journals: List[Union[str, datetime]]) -> None:
    """
    Process journal keys to build the complete timeline and detect missing entries.

    Args:
        journal_keys (List[str]): List of journal key strings.
        dangling_journals (List[Union[str, datetime]]): List of dangling link keys (either strings or datetime objects).
    """
    # Convert journal keys from strings to datetime objects
    processed_keys = []
    for key in journal_keys:
        try:
            date_obj = datetime.strptime(key, "%Y-%m-%d %A")
            processed_keys.append(date_obj)
        except ValueError as e:
            print(f"Skipping invalid journal key '{key}': {e}")
    processed_keys.sort()

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

    # Write out results to files.
    simple_write(
        "00___complete_timeline.txt", complete_timeline
    )  # Start to end of journals on file, with gaps filled in
    simple_write("01___processed_keys.txt", processed_keys)  # Start to end of journals on file
    simple_write(
        "02___dangling_journals.txt", dangling_journals
    )  # Start to end of journals referenced, but not on file
    simple_write(
        "03___missing_keys.txt", missing_keys
    )  # Start to end of gap journals not on file and not referenced anywhere

    # Summary statistics
    # print(f"Total dates in complete timeline: {len(complete_timeline)}")
    # print(f"Missing journal dates: {len(missing_keys)}")
    # print(f"Original journal keys count: {len(processed_keys)}")
    # print(f"Remaining dangling links: {len(dangling_links)}")

    timeline_start = get_least_recent_date(complete_timeline)
    timeline_end = get_most_recent_date(complete_timeline)
    dangling_start = get_least_recent_date(dangling_journals)
    dangling_end = get_most_recent_date(dangling_journals)
    days, weeks, months, years = get_date_ranges(timeline_end, timeline_start)

    print(f"First journal key on file: {timeline_start}")
    print(f"Last journal key on file: {timeline_end}")
    print(f"First dangling link journal key: {dangling_start}")
    print(f"Last dangling link journal key: {dangling_end}")
    print(f"Timeline range: {days} days, {weeks} weeks, {months} months, {years} years")

    if dangling_start < timeline_start:
        past_dangling_journals = get_dangling_journals_past(dangling_journals, timeline_start)
        simple_write(
            "99___past_dangling_journals.txt", past_dangling_journals
        )  # Start to end of journals referenced, but not on file
    if dangling_end > timeline_end:
        future_dangling_journals = get_dangling_journals_future(dangling_journals, timeline_end)
        simple_write(
            "99___future_dangling_journals.txt", future_dangling_journals
        )  # Start to end of journals referenced, but not on file


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


def simple_write(file, data):
    """Write data to a file."""
    with open(file, "w", encoding="utf-8") as f:
        for line in data:
            f.write(f"{line}\n")
