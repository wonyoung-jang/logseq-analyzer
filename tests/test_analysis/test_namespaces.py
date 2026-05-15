"""Tests for LogseqJournals."""

import pytest

from logseq_analyzer.service.analysis import LogseqNamespaces


@pytest.fixture
def logseq_namespaces() -> LogseqNamespaces:
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces()
