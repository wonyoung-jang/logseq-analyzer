import re

# Journal format data {cljs_format: py_format}
DATETIME_TOKEN_MAP = {
    # Year
    "yyyy": "%Y",  # 4-digit year, e.g. 1996
    "xxxx": "%Y",  # 4-digit year, e.g. 1996
    "yy": "%y",  # 2-digit year, e.g. 96
    "xx": "%y",  # 2-digit year, e.g. 96
    # Month
    "MMMM": "%B",  # Full month name, e.g. January
    "MMM": "%b",  # Abbreviated month name, e.g. Jan
    "MM": "%m",  # 2-digit month, e.g. 01, 12
    "M": "%#m",  # Month number (platform-dependent; on Windows consider "%#m")
    # Day
    "dd": "%d",  # 2-digit day of month, e.g. 09, 31
    "d": "%#d",  # Day of month (un-padded; platform-dependent; on Windows consider "%#d")
    "D": "%j",  # Day of year as zero-padded decimal (001-366)
    # Weekday
    "EEEE": "%A",  # Full weekday name, e.g. Tuesday
    "EEE": "%a",  # Abbreviated weekday name, e.g. Tue
    "EE": "%a",  # Abbreviated weekday name, e.g. Tue
    "E": "%a",  # Abbreviated weekday name, e.g. Tue
    "e": "%u",  # TODO or %w? ISO weekday number (1=Monday, 7=Sunday)
    # Hour (24-hour clock)
    "HH": "%H",  # Hour (00-23)
    "H": "%H",  # Hour (0-23; un-padded; platform-dependent)
    # Hour (12-hour clock)
    "hh": "%I",  # Hour (01-12)
    "h": "%I",  # Hour (1-12; un-padded; platform-dependent)
    # TODO Alternative hour tokens (not directly supported in Python)
    # "k": <custom>,   # Clockhour of day (1-24) – no direct mapping
    # "K": <custom>,   # Hour of halfday (0-11) – no direct mapping
    # Minute
    "mm": "%M",  # Minute (00-59)
    "m": "%#M",  # Minute (0-59; un-padded; platform-dependent)
    # Second
    "ss": "%S",  # Second (00-59)
    "s": "%#S",  # Second (0-59; un-padded; platform-dependent)
    # Fractional seconds
    "SSS": "%f",  # Microseconds (6 digits); may need to truncate to 3 digits for milliseconds
    # AM/PM
    "a": "%p",  # AM/PM marker (locale-dependent; note: also used for halfday token)
    "A": "%p",  # AM/PM marker in upper-case (post-processing may be needed)
    # Time zone
    "Z": "%z",  # Time zone offset, e.g. -0800
    "ZZ": "%z",  # Time zone offset; post-process to add a colon if needed
    # TODO Tokens without direct Python equivalents (require custom processing):
    # "G":  None,      # Era designator, e.g. AD
    # "C":  None,      # Century of era
    # "Y":  None,      # Year of era (similar to yyyy for positive years)
    # "x":  None,      # Weekyear (requires isocalendar() computation)
    # "w":  None,      # Week of weekyear (requires isocalendar() computation)
    # "o":  None,      # Ordinal suffix for day of month, e.g. st, nd, rd, th
}

DATETIME_TOKEN_PATTERN = re.compile("|".join(re.escape(k) for k in sorted(DATETIME_TOKEN_MAP, key=len, reverse=True)))
