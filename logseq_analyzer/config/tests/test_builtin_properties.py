import pytest
from ..builtin_properties import LogseqBuiltInProperties


@pytest.fixture
def builtin_properties():
    """Fixture for LogseqBuiltInProperties."""
    return LogseqBuiltInProperties()


@pytest.fixture
def builtin_properties_set():
    """Fixture for setting built-in properties."""
    builtin_properties_set_static = frozenset(
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
    return builtin_properties_set_static


def test_singleton(builtin_properties):
    """Test singleton behavior."""
    another_instance = LogseqBuiltInProperties()
    assert builtin_properties is another_instance, "LogseqBuiltInProperties should be a singleton."


def test_set_builtin_properties(builtin_properties):
    """Test setting built-in properties."""
    builtin_properties.set_builtin_properties()
    assert builtin_properties.built_in_properties is not None, "Built-in properties should be set."
    assert isinstance(builtin_properties.built_in_properties, frozenset), "Built-in properties should be a frozenset."


def test_set_builtin_properties_content(builtin_properties, builtin_properties_set):
    """Test the content of built-in properties."""
    builtin_properties.set_builtin_properties()
    assert builtin_properties.built_in_properties == builtin_properties_set, "Built-in properties content should match."


def test_split_builtin_user_properties(builtin_properties):
    """Test splitting built-in and user-defined properties."""
    builtin_properties.set_builtin_properties()
    properties = [
        "alias",
        "custom-id",
        "user-defined-property-1",
        "user-defined-property-2",
    ]
    result = builtin_properties.split_builtin_user_properties(properties)
    assert result["built_in"] == ["alias", "custom-id"], "Built-in properties should be correctly identified."
    assert result["user_props"] == [
        "user-defined-property-1",
        "user-defined-property-2",
    ], "User-defined properties should be correctly identified."
    assert len(result["built_in"]) + len(result["user_props"]) == len(
        properties
    ), "Total properties should match the input list."
    assert all(
        prop in builtin_properties.built_in_properties for prop in result["built_in"]
    ), "All built-in properties should be in the built-in properties set."
