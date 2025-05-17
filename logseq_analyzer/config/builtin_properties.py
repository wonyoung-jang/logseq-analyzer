"""
Logseq Built-in Properties Module
"""

BUILT_INS = frozenset(
    [
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
    ]
)


def split_builtin_user_properties(properties: list[str]) -> dict[str, list[str]]:
    """
    Helper function to split properties into built-in and user-defined.

    Args:
        properties (list[str]): List of properties to split.

    Returns:
        dict[str, list[str]]: Dictionary containing built-in and user-defined properties.
    """
    properties_dict = {
        "built_ins": [prop for prop in properties if prop in BUILT_INS],
        "user_props": [prop for prop in properties if prop not in BUILT_INS],
    }
    return properties_dict
