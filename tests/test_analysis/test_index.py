"""Test the FileIndex class."""

import pytest

from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


def test_file_index_initialization(file_index) -> None:
    """Test the initialization of FileIndex."""
    assert file_index._files == set()
    assert file_index._name_to_files == {}
    assert file_index._path_to_file == {}
