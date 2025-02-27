# import src.config as config
# Used in
# - src/app.py
# - src/helpers.py
# - src/keynames.py
# - src/summarydata.py

JOURNAL_PAGE_TITLE_FORMAT = "MMM do, yyyy"
JOURNAL_FILE_NAME_FORMAT = "yyyy_MM_dd"
ASSETS_DIRECTORY = "assets"  # static
DRAWS_DIRECTORY = "draws"  # static
JOURNALS_DIRECTORY = "journals"
PAGES_DIRECTORY = "pages"
WHITEBOARDS_DIRECTORY = "whiteboards"

OUTPUT_DIR_META = "__meta"
OUTPUT_DIR_GRAPH = "graph"
OUTPUT_DIR_SUMMARY = "summary"
OUTPUT_DIR_TEST = "test"

TOKEN_MAP = {
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
