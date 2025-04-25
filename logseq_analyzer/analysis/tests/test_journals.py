"""
Tests for LogseqJournals
"""

import pytest

from ..journals import LogseqJournals


@pytest.fixture
def logseq_journals():
    return LogseqJournals()


def test_singleton(logseq_journals):
    another_instance = LogseqJournals()
    assert logseq_journals is another_instance


def test_representation(logseq_journals):
    assert repr(logseq_journals) == "LogseqJournals()"
    assert str(logseq_journals) == "LogseqJournals"


def test_len(logseq_journals):
    assert len(logseq_journals) == 0
    logseq_journals.complete_timeline = ["2023-01-01", "2023-01-02"]
    assert len(logseq_journals) == 2
