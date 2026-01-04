"""Test the FileIndex class."""

from logseq_analyzer.analysis.index import FileIndex


def test_file_index_initialization(file_index: FileIndex) -> None:
    """Test the initialization of FileIndex."""
    assert len(file_index) == 0
