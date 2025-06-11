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
    cache = Cache(Path(Constant.CACHE_FILE))
    cache.open()
    yield cache
    cache.close(FileIndex())


def test_cache_initialization(cache):
    """Test the initialization of the Cache class."""
    assert cache.cache_path.exists()
    assert cache.cache is not None
