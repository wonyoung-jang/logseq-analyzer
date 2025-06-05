"""
Tests for LogseqGraph
"""

import pytest

from ..graph import LogseqGraph
from ...analysis.index import FileIndex


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_graph(file_index):
    return LogseqGraph(file_index)


def test_representation(logseq_graph):
    assert repr(logseq_graph) == "LogseqGraph()"
    assert str(logseq_graph) == "LogseqGraph"
