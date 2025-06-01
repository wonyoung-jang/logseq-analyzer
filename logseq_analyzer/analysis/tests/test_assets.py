import pytest

from ..assets import LogseqAssets, LogseqAssetsHls


@pytest.fixture
def logseq_assets():
    return LogseqAssets()


@pytest.fixture
def logseq_assets_hls():
    return LogseqAssetsHls()


def test_logseq_assets_singleton(logseq_assets):
    other_logseq_assets = LogseqAssets()
    assert logseq_assets is other_logseq_assets
    assert isinstance(logseq_assets, LogseqAssets)


def test_logseq_assets_hls_singleton(logseq_assets_hls):
    other_logseq_assets_hls = LogseqAssetsHls()
    assert logseq_assets_hls is other_logseq_assets_hls
    assert isinstance(logseq_assets_hls, LogseqAssetsHls)


def test_logseq_assets_representation(logseq_assets):
    assert repr(logseq_assets) == "LogseqAssets()"
    assert str(logseq_assets) == "LogseqAssets"


def test_logseq_assets_hls_representation(logseq_assets_hls):
    assert repr(logseq_assets_hls) == "LogseqAssetsHls()"
    assert str(logseq_assets_hls) == "LogseqAssetsHls"


def test_logseq_assets_initialization(logseq_assets):
    assert logseq_assets.backlinked == set()
    assert logseq_assets.not_backlinked == set()


def test_logseq_assets_hls_initialization(logseq_assets_hls):
    assert logseq_assets_hls.asset_mapping == {}
    assert logseq_assets_hls.backlinked == set()
    assert logseq_assets_hls.hls_bullets == set()
    assert logseq_assets_hls.not_backlinked == set()
