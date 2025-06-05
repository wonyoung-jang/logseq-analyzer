"""
Tests for LogseqJournals
"""

import pytest

from ..namespaces import LogseqNamespaces
from ...analysis.index import FileIndex


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_namespaces(file_index):
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces(file_index, dangling_links=set())


def test_ns_representation(logseq_namespaces):
    """Test string representation."""
    assert repr(logseq_namespaces) == "LogseqNamespaces()"
    assert str(logseq_namespaces) == "LogseqNamespaces"
