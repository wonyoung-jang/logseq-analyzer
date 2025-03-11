import re

# import src.config as config

# Logseq Analyzer configurations
DEFAULT_OUTPUT_DIR = "logseq-analyzer-output"  # static
DEFAULT_LOG_FILE = "logseq_analyzer.log"  # static
DEFAULT_TO_DELETE_DIR = "to_delete" # static

FILE_TYPE_ASSET = "asset"
FILE_TYPE_DRAW = "draw"
FILE_TYPE_JOURNAL = "journal"
FILE_TYPE_PAGE = "page"
FILE_TYPE_WHITEBOARD = "whiteboard"
FILE_TYPE_OTHER = "other"

NODE_TYPE_BRANCH = "branch"
NODE_TYPE_LEAF = "leaf"
NODE_TYPE_ROOT = "root"
NODE_TYPE_OTHER = "other-node"
NODE_TYPE_ORPHAN_GRAPH = "orphan-graph"
NODE_TYPE_ORPHAN_TRUE = "orphan-true"

OUTPUT_DIR_META = "_meta"
OUTPUT_DIR_GRAPH = "_graph"
OUTPUT_DIR_SUMMARY = "_summary"
OUTPUT_DIR_NAMESPACE = "_namespaces"
OUTPUT_DIR_EXTENSIONS = "extensions"
OUTPUT_DIR_NODES = "nodes"
OUTPUT_DIR_TYPES = "types"
OUTPUT_DIR_ASSETS = "assets"
OUTPUT_DIR_TEST = "test"

# Core Logseq folder structure
DEFAULT_LOGSEQ_DIR = "logseq"  # static
DEFAULT_BAK_DIR = "bak"  # static
DEFAULT_RECYCLE_DIR = ".recycle"  # static
DEFAULT_CONFIG_FILE = "config.edn"  # static
GLOBAL_CONFIG_FILE = ""

# Logseq's config.edn configurations (Default values)
JOURNAL_PAGE_TITLE_FORMAT = "MMM do, yyyy"
JOURNAL_FILE_NAME_FORMAT = "yyyy_MM_dd"

DIR_ASSETS = "assets"  # static
DIR_DRAWS = "draws"  # static
DIR_JOURNALS = "journals"
DIR_PAGES = "pages"
DIR_WHITEBOARDS = "whiteboards"

NAMESPACE_FORMAT = ":legacy"  # or ":triple-lowbar"
NAMESPACE_SEP = "/"  # static
NAMESPACE_FILE_SEP = "%2F"  # or "___"

CONFIG_EDN_DATA = {
    "journal_page_title_format": JOURNAL_PAGE_TITLE_FORMAT,
    "journal_file_name_format": JOURNAL_FILE_NAME_FORMAT,
    "journals_directory": DIR_JOURNALS,
    "pages_directory": DIR_PAGES,
    "whiteboards_directory": DIR_WHITEBOARDS,
    "file_name_format": NAMESPACE_FORMAT,
}

# Journal format data {cljs_format: py_format}
DATETIME_TOKEN_MAP = {
    # Year
    "yyyy": "%Y",  # 4-digit year, e.g. 1996
    "yy": "%y",  # 2-digit year, e.g. 96
    # Month
    "MMMM": "%B",  # Full month name, e.g. January
    "MMM": "%b",  # Abbreviated month name, e.g. Jan
    "MM": "%m",  # 2-digit month, e.g. 01, 12
    "M": "%-m",  # Month number (platform-dependent; on Windows consider "%#m")
    # Day
    "dd": "%d",  # 2-digit day of month, e.g. 09, 31
    "d": "%-d",  # Day of month (un-padded; platform-dependent; on Windows consider "%#d")
    "D": "%j",  # Day of year as zero-padded decimal (001-366)
    # Weekday
    "EEEE": "%A",  # Full weekday name, e.g. Tuesday
    "EEE": "%a",  # Abbreviated weekday name, e.g. Tue
    "e": "%u",  # ISO weekday number (1=Monday, 7=Sunday)
    # Hour (24-hour clock)
    "HH": "%H",  # Hour (00-23)
    "H": "%-H",  # Hour (0-23; un-padded; platform-dependent)
    # Hour (12-hour clock)
    "hh": "%I",  # Hour (01-12)
    "h": "%-I",  # Hour (1-12; un-padded; platform-dependent)
    # TODO Alternative hour tokens (not directly supported in Python)
    # "k": <custom>,   # Clockhour of day (1-24) – no direct mapping
    # "K": <custom>,   # Hour of halfday (0-11) – no direct mapping
    # Minute
    "mm": "%M",  # Minute (00-59)
    "m": "%-M",  # Minute (0-59; un-padded; platform-dependent)
    # Second
    "ss": "%S",  # Second (00-59)
    "s": "%-S",  # Second (0-59; un-padded; platform-dependent)
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

# Logseq built-in and hidden default properties
BUILT_IN_PROPERTIES = frozenset(
    {
        "alias",
        "aliases",
        "background_color",
        "background-color",
        "collapsed",
        "created_at",
        "created-at",
        "custom-id",
        "doing",
        "done",
        "exclude-from-graph-view",
        "filetags",
        "filters",
        "heading",
        "hl-color",
        "hl-page",
        "hl-stamp",
        "hl-type",
        "icon",
        "id",
        "last_modified_at",
        "last-modified-at",
        "later",
        "logseq.color",
        "logseq.macro-arguments",
        "logseq.macro-name",
        "logseq.order-list-type",
        "logseq.query/nlp-date",
        "logseq.table.borders",
        "logseq.table.compact",
        "logseq.table.headers",
        "logseq.table.hover",
        "logseq.table.max-width",
        "logseq.table.stripes",
        "logseq.table.version",
        "logseq.tldraw.page",
        "logseq.tldraw.shape",
        "logseq.tldraw.shape",
        "ls-type",
        "macro",
        "now",
        "public",
        "query-properties",
        "query-sort-by",
        "query-sort-desc",
        "query-table",
        "tags",
        "template-including-parent",
        "template",
        "title",
        "todo",
        "updated-at",
    }
)
