"""Test Cache class."""

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.adapter.cache import Cache
from logseq_analyzer.app import Constant
from logseq_analyzer.domain.model import FileIndex

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def cache() -> Iterator[Cache]:
    """Fixture to create a Cache object."""
    cache = Cache(Path(Constant.CACHE_FILE))
    yield cache
    cache.save(FileIndex())


def test_cache_initialization(cache: Cache) -> None:
    """Test the initialization of the Cache class."""
    assert cache.path.exists()
