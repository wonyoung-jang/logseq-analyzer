"""Tests for LogseqJournals."""

import datetime

import pytest

from logseq_analyzer.analysis.index import FileIndex
from logseq_analyzer.analysis.journals import LogseqJournals


@pytest.fixture
def logseq_journals(file_index: FileIndex) -> LogseqJournals:
    """Fixture for LogseqJournals."""
    return LogseqJournals(file_index, dangling_links=set())


def test_len(logseq_journals: LogseqJournals) -> None:
    """Test the __len__ method of LogseqJournals."""
    assert len(logseq_journals) == 0
    logseq_journals.sets.timeline = [
        datetime.datetime.min.replace(tzinfo=datetime.UTC),
        datetime.datetime.max.replace(tzinfo=datetime.UTC),
    ]
    assert len(logseq_journals) == 2
