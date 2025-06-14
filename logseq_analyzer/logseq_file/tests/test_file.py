"""
Test the LogseqFile class.
"""

from pathlib import Path
from tempfile import TemporaryFile

import pytest

from ..file import LogseqFile


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
    assert logseq_file.path.file == Path(temp_file)
    assert logseq_file.bullets is None
    assert logseq_file.data == {}
    assert logseq_file.node.has_backlinks is False
    assert logseq_file.node.backlinked is False
    assert logseq_file.node.backlinked_ns_only is False
    assert logseq_file.node.node_type == "other"


def test_hash(logseq_file):
    """Test the hash of LogseqFile."""
    assert hash(logseq_file) == hash(logseq_file.path.file.parts)


def test_equality(logseq_file, temp_file):
    """Test the equality of LogseqFile objects."""
    logseq_file_2 = LogseqFile(Path(temp_file))
    assert logseq_file == logseq_file_2
    assert logseq_file != "Not a LogseqFile object"
