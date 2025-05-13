"""
Test the LogseqFile class.
"""

from pathlib import Path
from tempfile import TemporaryFile
import pytest

from ..bullets import LogseqBullets
from ..file import LogseqFile
from ..name import LogseqFilename
from ..stats import LogseqFilestats


@pytest.fixture
def temp_file():
    """Fixture to create a temporary file for testing."""
    with TemporaryFile() as tmp_file:
        tmp_file.write(b"")
        tmp_file.seek(0)
        yield tmp_file.name


@pytest.fixture
def logseq_file(temp_file):
    """Fixture to create a LogseqFile object using a temporary file."""
    logseq_file_obj = LogseqFile(Path(temp_file))
    return logseq_file_obj


def test_logseq_file(logseq_file, temp_file):
    """Test the LogseqFile functionality."""
    assert logseq_file.file_path == Path(temp_file)
    assert logseq_file.is_backlinked == False
    assert logseq_file.is_backlinked_by_ns_only == False
    assert logseq_file.node_type == "other"
    assert logseq_file.file_type == "other"
    assert isinstance(logseq_file.path, LogseqFilename)
    assert isinstance(logseq_file.stat, LogseqFilestats)
    assert isinstance(logseq_file.bullets, LogseqBullets)


def test_representation(logseq_file):
    """Test the string representation of LogseqFile."""
    assert repr(logseq_file) == f'LogseqFile(file_path="{logseq_file.file_path}")'
    assert str(logseq_file) == f"LogseqFile: {logseq_file.file_path}"


def test_hash(logseq_file):
    """Test the hash of LogseqFile."""
    assert hash(logseq_file) == hash(logseq_file.path.parts)


def test_equality(logseq_file, temp_file):
    """Test the equality of LogseqFile objects."""
    logseq_file_2 = LogseqFile(Path(temp_file))
    assert logseq_file == logseq_file_2
    assert logseq_file != "Not a LogseqFile object"
