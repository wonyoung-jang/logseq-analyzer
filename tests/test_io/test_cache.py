"""Test Cache class."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.analysis.index import FileIndex
from logseq_analyzer.app import Constant
from logseq_analyzer.io.cache import Cache

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def cache() -> Iterator[Cache]:
    """Fixture to create a Cache object."""
    cache = Cache(Path(Constant.CACHE_FILE))
    cache.open()
    yield cache
    cache.close(FileIndex())


def test_cache_initialization(cache: Cache) -> None:
    """Test the initialization of the Cache class."""
    assert cache.path.exists()
    assert cache.cache is not None
