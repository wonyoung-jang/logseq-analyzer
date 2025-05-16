import pytest

from ..assets import LogseqAssets, LogseqAssetsHls


@pytest.fixture
def logseq_assets():
    return LogseqAssets()


@pytest.fixture
def logseq_assets_hls():
    return LogseqAssetsHls()


def test_len(logseq_assets):
    assert len(logseq_assets) == 0
    logseq_assets.backlinked = ["a", "b"]
    logseq_assets.not_backlinked = ["c"]
    assert len(logseq_assets) == 3
    logseq_assets.backlinked = []
    logseq_assets.not_backlinked = []


def test_logseq_assets_singleton(logseq_assets):
    other_logseq_assets = LogseqAssets()
    assert logseq_assets is other_logseq_assets
    assert isinstance(logseq_assets, LogseqAssets)


def test_logseq_assets_hls_singleton(logseq_assets_hls):
    other_logseq_assets_hls = LogseqAssetsHls()
    assert logseq_assets_hls is other_logseq_assets_hls
    assert isinstance(logseq_assets_hls, LogseqAssetsHls)


def test_logseq_assets_initialization(logseq_assets):
    assert logseq_assets.backlinked == []
    assert logseq_assets.not_backlinked == []


def test_logseq_assets_hls_initialization(logseq_assets_hls):
    assert logseq_assets_hls.asset_mapping == {}
    assert logseq_assets_hls.asset_names == set()
    assert logseq_assets_hls.backlinked == set()
    assert logseq_assets_hls.formatted_bullets == set()
    assert logseq_assets_hls.not_backlinked == set()
