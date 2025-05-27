"""
Tests for LogseqJournals
"""

import pytest

from ..index import FileIndex
from ..namespaces import LogseqNamespaces


@pytest.fixture
def logseq_namespaces():
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces(FileIndex())


def test_singleton(logseq_namespaces):
    """Test singleton behavior."""
    another_instance = LogseqNamespaces()
    assert logseq_namespaces is another_instance


def test_ns_representation(logseq_namespaces):
    """Test string representation."""
    assert repr(logseq_namespaces) == "LogseqNamespaces()"
    assert str(logseq_namespaces) == "LogseqNamespaces"
