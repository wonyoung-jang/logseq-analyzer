"""Test the LogseqFile class."""

from pathlib import Path
from tempfile import TemporaryFile
from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.domain.model import LogseqFile, _process_aliases

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def temp_file() -> Iterator[str]:
    """Fixture to create a temporary file for testing."""
    with TemporaryFile() as tmp_file:
        tmp_file.write(b"")
        tmp_file.seek(0)
        yield tmp_file.name


@pytest.fixture
def logseq_file(temp_file: str) -> LogseqFile:
    """Fixture to create a LogseqFile object using a temporary file."""
    return LogseqFile(Path(temp_file), "test_file", "page", {})


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
