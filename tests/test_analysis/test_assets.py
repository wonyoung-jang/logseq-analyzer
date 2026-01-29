"""Test the LogseqAssets and LogseqAssetsHls classes."""

from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.analysis.assets import LogseqAssets, LogseqAssetsHls

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def logseq_assets(file_index: FileIndex) -> LogseqAssets:
    """Fixture for LogseqAssets."""
    return LogseqAssets(file_index)


@pytest.fixture
def logseq_assets_hls(file_index: FileIndex) -> LogseqAssetsHls:
    """Fixture for LogseqAssetsHls."""
    return LogseqAssetsHls(file_index)


def test_logseq_assets_initialization(logseq_assets: LogseqAssets) -> None:
    """Test the initialization of LogseqAssets."""
    assert logseq_assets.backlinked == set()
    assert logseq_assets.not_backlinked == set()


def test_logseq_assets_hls_initialization(logseq_assets_hls: LogseqAssetsHls) -> None:
    """Test the initialization of LogseqAssetsHls."""
    assert logseq_assets_hls.asset_mapping == {}
    assert logseq_assets_hls.backlinked == set()
    assert logseq_assets_hls.hls_bullets == set()
    assert logseq_assets_hls.not_backlinked == set()
