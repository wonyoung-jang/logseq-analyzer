import pytest
from ..builtin_properties import split_builtin_user_properties, BUILT_INS


@pytest.fixture
def builtin_properties_set_static():
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


def test_set_builtin_properties_content(builtin_properties_set_static):
    """Test the content of built-in properties."""
    assert builtin_properties_set_static == BUILT_INS, "Built-in properties content should match."


def test_split_builtin_user_properties(builtin_properties_set_static):
    """Test splitting built-in and user-defined properties."""
    properties = set(
        [
            "alias",
            "custom-id",
            "user-defined-property-1",
            "user-defined-property-2",
        ]
    )
    result = split_builtin_user_properties(properties)
    assert result["built_ins"] == ["alias", "custom-id"], "Built-in properties should be correctly identified."
    assert result["user_props"] == [
        "user-defined-property-1",
        "user-defined-property-2",
    ], "User-defined properties should be correctly identified."
    assert len(result["built_ins"]) + len(result["user_props"]) == len(
        properties
    ), "Total properties should match the input list."
    assert all(
        prop in builtin_properties_set_static for prop in result["built_ins"]
    ), "All built-in properties should be in the built-in properties set."
