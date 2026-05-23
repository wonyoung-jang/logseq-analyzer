"""Test the LogseqFile class."""

import pytest

from logseq_analyzer.domain.model import _process_aliases


@pytest.mark.parametrize(
    ("input_str", "expected"),
    [
        # existing
        ("a,b,c", ["a", "b", "c"]),
        ("  A  ,  B  ", ["a", "b"]),
        ("[[a,b]],c", ["a,b", "c"]),
        ("alias1 [[alias2,alias3]], alias4", ["alias1 alias2,alias3", "alias4"]),
        ("x,,y,", ["x", "y"]),
        # empty / whitespace
        ("", []),
        ("   ", []),
        (",,,", []),
        # plain bracket only
        ("[[foo bar]]", ["foo bar"]),
        ("[[foo, bar]]", ["foo, bar"]),
        # bracket adjacency
        ("[[alpha]], beta", ["alpha", "beta"]),
        ("beta, [[alpha]]", ["beta", "alpha"]),
        ("[[a, b]], c, [[d, e]]", ["a, b", "c", "d, e"]),
        ("[[x]],[[y]]", ["x", "y"]),
        # normalisation
        ("Foo, BAR, [[Baz Qux]]", ["foo", "bar", "baz qux"]),
        ("[[  spaced  ]]", ["spaced"]),
    ],
)
def test_process_aliases(input_str: str, expected: list[str]) -> None:
    """Test the _process_aliases function with various input strings."""
    assert list(_process_aliases(input_str)) == expected
