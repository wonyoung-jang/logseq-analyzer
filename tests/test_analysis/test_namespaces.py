"""Tests for LogseqJournals."""

from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.analysis.namespaces import LogseqNamespaces

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def logseq_namespaces(file_index: FileIndex) -> LogseqNamespaces:
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces(file_index, dangling_links=set())
