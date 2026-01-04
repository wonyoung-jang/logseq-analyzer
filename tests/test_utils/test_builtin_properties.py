"""Tests for built-in properties in utils module."""

import pytest

from logseq_analyzer.utils.helpers import BUILT_IN_PROPERTIES


@pytest.fixture
def builtin_properties_set_static() -> frozenset[str]:
    """Fixture for setting built-in properties."""
    return frozenset(
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


def test_set_builtin_properties_content(builtin_properties_set_static: frozenset[str]) -> None:
    """Test the content of built-in properties."""
    assert builtin_properties_set_static == BUILT_IN_PROPERTIES, "Built-in properties content should match."
