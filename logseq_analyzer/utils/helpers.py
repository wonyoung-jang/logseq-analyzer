"""Helper functions for file and date processing."""

from collections import Counter

BUILT_IN_PROPERTIES: frozenset[str] = frozenset(
    (
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
    )
)


def sort_dict_by_value(data: dict, value: str = "", *, reverse: bool = False) -> dict:
    """Sort a dictionary by its values."""
    if value:
        return dict(sorted(data.items(), key=lambda item: item[1][value], reverse=reverse))
    return dict(sorted(data.items(), key=lambda item: item[1], reverse=reverse))


def get_count_and_foundin_data(result: dict, collection: list[str], filename: str) -> dict:
    """Update the result dictionary with counts and file occurrences.

    Args:
        result (dict): The dictionary to update with counts and file occurrences.
        collection (list[str]): The collection of items to count.
        filename (str): The name of the file containing the path information.

    Returns:
        dict: The updated result dictionary with counts and file occurrences.

    """
    for item in collection:
        result.setdefault(
            item,
            {"count": 0, "found_in": Counter()},
        )
        result[item]["count"] = result[item].get("count", 0) + 1
        result[item]["found_in"][filename] += 1
    return result
