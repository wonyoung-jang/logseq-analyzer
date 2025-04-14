"""
Tests for LogseqGraph
"""

import pytest

from ..graph import LogseqGraph


@pytest.fixture
def logseq_graph():
    return LogseqGraph()


def test_singleton(logseq_graph):
    another_instance = LogseqGraph()
    assert logseq_graph is another_instance
