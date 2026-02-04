"""Tests for LogseqGraph."""

from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.analysis.graph import LogseqGraph

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def logseq_graph(file_index: FileIndex) -> LogseqGraph:
    """Fixture for LogseqGraph."""
    return LogseqGraph(file_index)
