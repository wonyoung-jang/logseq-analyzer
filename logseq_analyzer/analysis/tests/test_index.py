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


def test_file_index_representation(file_index):
    """Test the string representation of FileIndex."""
    assert repr(file_index) == "FileIndex()"
    assert str(file_index) == "FileIndex"


def test_file_index_initialization(file_index):
    """Test the initialization of FileIndex."""
    assert file_index._files == set()
    assert file_index._hash_to_file == {}
    assert file_index._name_to_files == {}
    assert file_index._path_to_file == {}
