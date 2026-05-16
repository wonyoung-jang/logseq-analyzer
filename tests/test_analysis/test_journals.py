"""Tests for LogseqJournals."""

import datetime

import pytest

from logseq_analyzer.service.analysis import LogseqJournals


@pytest.fixture
def logseq_journals() -> LogseqJournals:
    """Fixture for LogseqJournals."""
    return LogseqJournals()


def test_len(logseq_journals: LogseqJournals) -> None:
    """Test the __len__ method of LogseqJournals."""
    assert len(logseq_journals) == 0
    logseq_journals.existing_timeline = [
        datetime.datetime.min.replace(tzinfo=datetime.UTC),
        datetime.datetime.max.replace(tzinfo=datetime.UTC),
    ]
    assert len(logseq_journals) == 2
