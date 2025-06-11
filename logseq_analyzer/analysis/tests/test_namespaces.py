"""
Tests for LogseqJournals
"""

import pytest

from ...analysis.index import FileIndex
from ..namespaces import LogseqNamespaces


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_namespaces(file_index):
    """Fixture for LogseqNamespaces."""
    return LogseqNamespaces(file_index, dangling_links=set())
