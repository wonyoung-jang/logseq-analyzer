import pytest

from logseq_analyzer.analysis.assets import LogseqAssets, LogseqAssetsHls
from logseq_analyzer.analysis.index import FileIndex


@pytest.fixture
def file_index():
    """Fixture to create a FileIndex object."""
    return FileIndex()


@pytest.fixture
def logseq_assets(file_index):
    return LogseqAssets(file_index)


@pytest.fixture
def logseq_assets_hls(file_index):
    return LogseqAssetsHls(file_index)


def test_logseq_assets_initialization(logseq_assets) -> None:
    assert logseq_assets.backlinked == set()
    assert logseq_assets.not_backlinked == set()


def test_logseq_assets_hls_initialization(logseq_assets_hls) -> None:
    assert logseq_assets_hls.asset_mapping == {}
    assert logseq_assets_hls.backlinked == set()
    assert logseq_assets_hls.hls_bullets == set()
    assert logseq_assets_hls.not_backlinked == set()
