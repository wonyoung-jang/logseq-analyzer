from pathlib import Path
import pytest
from ..filesystem import File


@pytest.fixture
def fs():
    return File


# Test the File class
def test_file_class(fs):
    assert isinstance(fs(), File)
    assert fs().path is None
