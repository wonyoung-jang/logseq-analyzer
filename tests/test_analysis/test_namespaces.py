"""Tests for LogseqJournals."""

import pytest

from logseq_analyzer.analysis.index import FileIndex
from logseq_analyzer.analysis.namespaces import LogseqNamespaces


@pytest.fixture
def logseq_namespaces(file_index: FileIndex) -> LogseqNamespaces:
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces(file_index, dangling_links=set())
