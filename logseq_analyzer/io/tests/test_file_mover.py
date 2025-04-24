"""
Test LogseqFileMover class.
"""

import pytest

from ..file_mover import LogseqFileMover


@pytest.fixture
def logseq_file_mover():
    """Fixture to create a LogseqFileMover object."""
    return LogseqFileMover()


def test_logseq_file_mover_init(logseq_file_mover):
    """Test the initialization of LogseqFileMover."""
    assert logseq_file_mover.moved_files == {}
    assert logseq_file_mover.delete is not None


def test_file_mover_singleton(logseq_file_mover):
    """Test the singleton behavior of LogseqFileMover."""
    another_instance = LogseqFileMover()
    assert logseq_file_mover is another_instance
