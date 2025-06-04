"""
Test Cache class.
"""

import pytest
from pathlib import Path

from ..cache import Cache
from ...utils.enums import Constants


@pytest.fixture
def cache():
    """Fixture to create a Cache object."""
    cache = Cache(Path(Constants.CACHE_FILE.value))
    cache.open()
    yield cache
    cache.close()


def test_cache_initialization(cache):
    """Test the initialization of the Cache class."""
    assert cache.cache_path.exists()
    assert cache.cache is not None


def test_representation(cache):
    """Test the string representation of Cache."""
    assert repr(cache) == f'Cache(cache_path="{cache.cache_path}")'
    assert str(cache) == f"Cache: {cache.cache_path}"
