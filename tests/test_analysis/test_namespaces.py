"""Tests for LogseqJournals."""

import pytest

from logseq_analyzer.analysis.index import FileIndex
from logseq_analyzer.analysis.namespaces import LogseqNamespaces


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_namespaces(file_index):
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces(file_index, dangling_links=set())
