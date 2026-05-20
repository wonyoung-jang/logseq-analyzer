"""Tests for LogseqJournals."""

import pytest

from logseq_analyzer.service.analysis import LogseqJournals


@pytest.fixture
def logseq_journals() -> LogseqJournals:
    """Fixture for LogseqJournals."""
    return LogseqJournals()
