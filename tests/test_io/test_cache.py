"""Test Cache class."""

from pathlib import Path

import pytest

from logseq_analyzer.analysis.index import FileIndex
from logseq_analyzer.io.cache import Cache
from logseq_analyzer.utils.enums import Constant


@pytest.fixture
def cache():
    """Fixture to create a Cache object."""
    cache = Cache(Path(Constant.CACHE_FILE))
    cache.open()
    yield cache
    cache.close(FileIndex())


def test_cache_initialization(cache) -> None:
    """Test the initialization of the Cache class."""
    assert cache.cache_path.exists()
    assert cache.cache is not None
