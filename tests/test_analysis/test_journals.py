"""Tests for LogseqJournals."""

import pytest

from logseq_analyzer.analysis.index import FileIndex
from logseq_analyzer.analysis.journals import LogseqJournals


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_journals(file_index):
    return LogseqJournals(file_index, dangling_links=set())


def test_len(logseq_journals) -> None:
    assert len(logseq_journals) == 0
    logseq_journals.sets.timeline = ["2023-01-01", "2023-01-02"]
    assert len(logseq_journals) == 2
