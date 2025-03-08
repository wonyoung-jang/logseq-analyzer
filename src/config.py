import re

# import src.config as config

# Logseq Analyzer configurations
DEFAULT_OUTPUT_DIR = "logseq-analyzer-output"
DEFAULT_LOG_FILE = "logseq_analyzer.log"
DEFAULT_TO_DELETE_DIR = "to_delete"

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

OUTPUT_DIR_META = "__meta"
OUTPUT_DIR_GRAPH = "graph"
OUTPUT_DIR_SUMMARY = "summary"
OUTPUT_DIR_NAMESPACE = "namespace"
OUTPUT_DIR_TEST = "test"

# Core Logseq folder structure
DEFAULT_LOGSEQ_DIR = "logseq"  # static
DEFAULT_BAK_DIR = "bak"  # static
DEFAULT_RECYCLE_DIR = ".recycle"  # static
DEFAULT_CONFIG_FILE = "config.edn"  # static
GLOBAL_CONFIG_FILE = ""

# Logseq's config.edn configurations
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

# Journal format data
DATETIME_TOKEN_MAP = {
    "yyyy": "%Y",
    "yy": "%y",
    "MMMM": "%B",
    "MMM": "%b",
    "MM": "%m",
    "M": "%-m",
    "dd": "%d",
    "d": "%-d",
    "EEEE": "%A",
    "EEE": "%a",
}
DATETIME_TOKEN_PATTERN = re.compile("|".join(re.escape(k) for k in sorted(DATETIME_TOKEN_MAP, key=len, reverse=True)))

# Logseq built-in and hidden default properties
BUILT_IN_PROPERTIES = {
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
