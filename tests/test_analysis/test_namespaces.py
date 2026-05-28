"""Tests for LogseqJournals."""

import pytest

from logseq_analyzer.service.analysis import LogseqNamespaceConflicts


@pytest.fixture
def logseq_namespaces() -> LogseqNamespaceConflicts:
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaceConflicts()
