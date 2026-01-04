"""Tests for LogseqGraph."""

import pytest

from logseq_analyzer.analysis.graph import LogseqGraph
from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_graph(file_index):
    return LogseqGraph(file_index)
