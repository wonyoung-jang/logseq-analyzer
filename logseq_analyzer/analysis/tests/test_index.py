"""
Test the FileIndex class.
"""

import pytest

from ..index import FileIndex


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


def test_file_index_singleton(file_index):
    """Test the singleton behavior of FileIndex."""
    another_index = FileIndex()
    assert file_index is another_index, "FileIndex should be a singleton."


def test_file_index_initialization(file_index):
    """Test the initialization of FileIndex."""
    assert file_index.files == set()
    assert file_index.hash_to_file == {}
    assert file_index.name_to_files == {}
    assert file_index.path_to_file == {}
