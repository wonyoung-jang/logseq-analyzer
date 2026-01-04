"""Unit tests for helpers.py module."""

import pytest

from logseq_analyzer.utils.helpers import process_aliases


@pytest.mark.parametrize(
    ("input_str", "expected"),
    [
        ("a,b,c", ["a", "b", "c"]),
        ("  A  ,  B  ", ["a", "b"]),
        ("[[a,b]],c", ["a,b", "c"]),
        ("alias1 [[alias2,alias3]], alias4", ["alias1 alias2,alias3", "alias4"]),
        ("x,,y,", ["x", "y"]),
    ],
)
def test_process_aliases_various(input_str, expected) -> None:
    assert list(process_aliases(input_str)) == expected
