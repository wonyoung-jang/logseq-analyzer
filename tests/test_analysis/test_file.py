"""Test the LogseqFile class."""

from pathlib import Path
from tempfile import TemporaryFile
from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.domain.model import (
    JournalFormats,
    LogseqFile,
    LogseqFileContext,
    _format_bytes,
    _process_aliases,
)

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, "0 B"),
        (1, "1 B"),
        (1023, "1023 B"),
        (1024, "1.00 KB"),
        (2048, "2.00 KB"),
        (1048576, "1.00 MB"),
        (1073741824, "1.00 GB"),
        (1099511627776, "1.00 TB"),
        (1125899906842624, "1.00 PB"),
    ],
)
def test_format_bytes_iec(value: int, expected: str) -> None:
    """Test the format_bytes function with IEC units."""
    assert _format_bytes(value) == expected


@pytest.fixture
def temp_file() -> Iterator[str]:
    """Fixture to create a temporary file for testing."""
    with TemporaryFile() as tmp_file:
        tmp_file.write(b"")
        tmp_file.seek(0)
        yield tmp_file.name


@pytest.fixture
def logseq_file_context() -> LogseqFileContext:
    """Fixture to create a LogseqFileContext object for testing."""
    return LogseqFileContext(
        now_ts=0.0,
        journal_format=JournalFormats(
            file="{{year}}/{{month}}/{{day}}.md",
            page="{{name}}.md",
            page_title="{{name}}",
        ),
        ns_file_sep="__",
        journal_dir="journals",
        graph_path=Path("test_graph"),
        filetype_map={},
    )


@pytest.fixture
def logseq_file(temp_file: str, logseq_file_context: LogseqFileContext) -> LogseqFile:
    """Fixture to create a LogseqFile object using a temporary file."""
    return LogseqFile(Path(temp_file), context=logseq_file_context)


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
def test_process_aliases_various(input_str: str, expected: list[str]) -> None:
    """Test process_aliases with various inputs."""
    assert list(_process_aliases(input_str)) == expected
