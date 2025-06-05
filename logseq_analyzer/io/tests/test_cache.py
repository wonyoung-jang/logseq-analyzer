"""
Test Cache class.
"""

from pathlib import Path

import pytest

from ...analysis.index import FileIndex
from ...utils.enums import Constant
from ..cache import Cache


@pytest.fixture
def cache():
    """Fixture to create a Cache object."""
    cache = Cache(Path(Constant.CACHE_FILE.value))
    cache.open()
    yield cache
    cache.close(FileIndex())


def test_cache_initialization(cache):
    """Test the initialization of the Cache class."""
    assert cache.cache_path.exists()
    assert cache.cache is not None


def test_representation(cache):
    """Test the string representation of Cache."""
    assert repr(cache) == f'Cache(cache_path="{cache.cache_path}")'
    assert str(cache) == f"Cache: {cache.cache_path}"
