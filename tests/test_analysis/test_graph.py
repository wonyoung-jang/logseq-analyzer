"""Tests for LogseqGraph."""

import pytest

from logseq_analyzer.analysis.graph import LogseqGraph
from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def logseq_graph(file_index: FileIndex) -> LogseqGraph:
    """Fixture for LogseqGraph."""
    return LogseqGraph(file_index)
