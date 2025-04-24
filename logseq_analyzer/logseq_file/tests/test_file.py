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
    assert logseq_file.masked_blocks == {}
    assert logseq_file.content == ""
    assert logseq_file.primary_bullet == ""
    assert logseq_file.content_bullets == []
    assert logseq_file.has_content == False
    assert logseq_file.is_backlinked == False
    assert logseq_file.is_backlinked_by_ns_only == False
    assert logseq_file.node_type == "other"
    assert logseq_file.file_type == "other"
    assert isinstance(logseq_file.path, LogseqFilename)
    assert isinstance(logseq_file.stat, LogseqFilestats)
    assert isinstance(logseq_file.bullets, LogseqBullets)
