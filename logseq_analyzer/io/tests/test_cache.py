"""
Test Cache class.
"""

import pytest

from ..cache import Cache


@pytest.fixture
def cache():
    """Fixture to create a Cache object."""
    cache = Cache()
    yield cache
    cache.close()


def test_cache_initialization(cache):
    """Test the initialization of the Cache class."""
    assert cache.cache_path.exists()
    assert cache.cache is not None


def test_cache_singleton(cache):
    """Test the singleton behavior of the Cache class."""
    another_cache = Cache()
    assert cache is another_cache, "Cache should be a singleton."
