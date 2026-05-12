"""Fixtures for testing."""

import pytest

from logseq_analyzer.domain.model import FileIndex


@pytest.fixture
def file_index() -> FileIndex:
    """Fixture to create a FileIndex object."""
    return FileIndex()
