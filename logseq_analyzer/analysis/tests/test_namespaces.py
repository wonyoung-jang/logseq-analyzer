"""
Tests for LogseqJournals
"""

import pytest

from ..namespaces import LogseqNamespaces


@pytest.fixture
def logseq_namespaces():
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces()


def test_singleton(logseq_namespaces):
    """Test singleton behavior."""
    another_instance = LogseqNamespaces()
    assert logseq_namespaces is another_instance


def test_len(logseq_namespaces):
    """Test length of unique namespace parts."""
    assert len(logseq_namespaces) == 0
    logseq_namespaces.namespace_data = {"namespace1": {}, "namespace2": {}}
    assert len(logseq_namespaces) == 2
