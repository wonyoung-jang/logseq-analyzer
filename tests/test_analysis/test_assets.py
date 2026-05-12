"""Test the LogseqAssets and LogseqAssetsHls classes."""

from typing import TYPE_CHECKING

import pytest

from logseq_analyzer.service.analysis import LogseqAssets

if TYPE_CHECKING:
    from logseq_analyzer.domain.model import FileIndex


@pytest.fixture
def logseq_assets(file_index: FileIndex) -> LogseqAssets:
    """Fixture for LogseqAssets."""
    return LogseqAssets(file_index)


@pytest.fixture
def logseq_assets_hls(file_index: FileIndex) -> LogseqAssets:
    """Fixture for LogseqAssetsHls."""
    return LogseqAssets(file_index)


def test_logseq_assets_initialization(logseq_assets: LogseqAssets) -> None:
    """Test the initialization of LogseqAssets."""
    assert logseq_assets.backlinked == set()
    assert logseq_assets.not_backlinked == set()


def test_logseq_assets_hls_initialization(logseq_assets_hls: LogseqAssets) -> None:
    """Test the initialization of LogseqAssetsHls."""
    assert logseq_assets_hls.asset_mapping == {}
    assert logseq_assets_hls.backlinked_hls == set()
    assert logseq_assets_hls.hls_bullets == set()
    assert logseq_assets_hls.not_backlinked_hls == set()
