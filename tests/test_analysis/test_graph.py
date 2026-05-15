"""Tests for LogseqGraph."""

import pytest

from logseq_analyzer.service.analysis import LogseqGraph


@pytest.fixture
def logseq_graph() -> LogseqGraph:
    """Fixture for LogseqGraph."""
    return LogseqGraph()
