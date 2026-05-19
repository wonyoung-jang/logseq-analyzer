"""Test the LogseqAssets and LogseqAssetsHls classes."""

import pytest

from logseq_analyzer.service.analysis import LogseqAssets


@pytest.fixture
def logseq_assets() -> LogseqAssets:
    """Fixture for LogseqAssets."""
    return LogseqAssets()


def test_logseq_assets_initialization(logseq_assets: LogseqAssets) -> None:
    """Test the initialization of LogseqAssets."""
    assert logseq_assets.backlinked == set()
    assert logseq_assets.not_backlinked == set()
    assert logseq_assets.hls_map == {}
    assert logseq_assets.hls_backlinked == set()
    assert logseq_assets.hls_not_backlinked == set()
    assert logseq_assets.hls_bullet == set()
