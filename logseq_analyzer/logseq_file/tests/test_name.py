"""
Test for LogseqFilename class.
"""

import pytest
from pathlib import Path
from tempfile import TemporaryFile

from ..name import LogseqFilename


@pytest.fixture
def temp_file():
    """Fixture to create a temporary file for testing."""
    with TemporaryFile() as tmp_file:
        tmp_file.write(b"Test content")
        tmp_file.seek(0)
        yield tmp_file.name


@pytest.fixture
def logseq_filename(temp_file):
    """Fixture to create a LogseqFilename object using a temporary file."""
    filename_obj = LogseqFilename(Path(temp_file))
    return filename_obj


def test_logseq_filename(logseq_filename, temp_file):
    """Test the LogseqFilename functionality."""
    assert logseq_filename.file_path == Path(temp_file)
    assert logseq_filename.name == Path(temp_file).stem
    assert logseq_filename.parent == Path(temp_file).parent.name
    assert logseq_filename.suffix == Path(temp_file).suffix
    assert logseq_filename.parts == Path(temp_file).parts
    assert logseq_filename.uri == Path(temp_file).as_uri()
