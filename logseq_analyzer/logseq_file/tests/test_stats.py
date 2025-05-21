"""
Tests for LogseqFilestats
"""

from pathlib import Path
from tempfile import TemporaryFile
import pytest

from ..stats import LogseqFilestats


@pytest.fixture
def temp_file():
    """Fixture to create a temporary file for testing."""
    with TemporaryFile() as tmp_file:
        tmp_file.write(b"Test content")
        tmp_file.seek(0)
        yield tmp_file.name


@pytest.fixture
def logseq_filestats(temp_file):
    """Fixture to create a LogseqFilestats object using a temporary file."""
    stats = LogseqFilestats(Path(temp_file))
    return stats


def test_logseq_filestats(logseq_filestats, temp_file):
    """Test the LogseqFilestats functionality."""
    assert logseq_filestats.file_path == Path(temp_file)
    assert logseq_filestats.size == 0
    assert logseq_filestats.has_content == False
    assert logseq_filestats.time_existed == 0.0
    assert logseq_filestats.time_unmodified == 0.0
    assert logseq_filestats.date_created is not None
    assert logseq_filestats.date_modified is not None
    assert isinstance(logseq_filestats.date_created, str)
    assert isinstance(logseq_filestats.date_modified, str)
