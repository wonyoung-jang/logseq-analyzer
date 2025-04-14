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
