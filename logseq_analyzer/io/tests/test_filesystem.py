from pathlib import Path
import pytest

from ..filesystem import (
    AssetsDirectory,
    BakDirectory,
    CacheFile,
    ConfigFile,
    DeleteAssetsDirectory,
    DeleteBakDirectory,
    DeleteDirectory,
    DeleteRecycleDirectory,
    DrawsDirectory,
    File,
    GlobalConfigFile,
    GraphDirectory,
    JournalsDirectory,
    LogFile,
    LogseqDirectory,
    OutputDirectory,
    PagesDirectory,
    RecycleDirectory,
    WhiteboardsDirectory,
)


@pytest.fixture
def generic_file():
    return File("test.txt")


@pytest.fixture
def output_dir():
    return OutputDirectory()


@pytest.fixture
def log_file():
    return LogFile()


@pytest.fixture
def graph_dir():
    return GraphDirectory()


@pytest.fixture
def logseq_dir():
    return LogseqDirectory()


@pytest.fixture
def config_file():
    return ConfigFile()


@pytest.fixture
def delete_dir():
    return DeleteDirectory()


@pytest.fixture
def delete_bak_dir():
    return DeleteBakDirectory()


@pytest.fixture
def delete_recycle_dir():
    return DeleteRecycleDirectory()


@pytest.fixture
def delete_assets_dir():
    return DeleteAssetsDirectory()


@pytest.fixture
def cache_file():
    return CacheFile()


@pytest.fixture
def bak_dir():
    return BakDirectory()


@pytest.fixture
def recycle_dir():
    return RecycleDirectory()


@pytest.fixture
def global_config_file():
    return GlobalConfigFile()


@pytest.fixture
def assets_dir():
    return AssetsDirectory()


@pytest.fixture
def draws_dir():
    return DrawsDirectory()


@pytest.fixture
def journals_dir():
    return JournalsDirectory()


@pytest.fixture
def pages_dir():
    return PagesDirectory()


@pytest.fixture
def whiteboards_dir():
    return WhiteboardsDirectory()


def test_file_initialization(generic_file):
    """Test that the File class is initialized correctly."""
    assert generic_file.path == Path("test.txt")
    assert generic_file.path.exists() is False
    assert generic_file.path.is_dir() is False
    assert generic_file.path.is_file() is False


def test_representation(generic_file):
    """Test the string representation of the File class."""
    assert repr(generic_file) == 'File(path="test.txt")'
    assert str(generic_file) == "File: test.txt"


def test_output_dir_singleton(output_dir):
    """Test that the LogseqAnalyzerOutputDir is a singleton."""
    other_output_dir = OutputDirectory()
    assert output_dir is other_output_dir
    assert isinstance(output_dir, OutputDirectory)


def test_log_file_singleton(log_file):
    """Test that the LogseqAnalyzerLogFile is a singleton."""
    other_log_file = LogFile()
    assert log_file is other_log_file
    assert isinstance(log_file, LogFile)


def test_graph_dir_singleton(graph_dir):
    """Test that the LogseqAnalyzerGraphDir is a singleton."""
    other_graph_dir = GraphDirectory()
    assert graph_dir is other_graph_dir
    assert isinstance(graph_dir, GraphDirectory)


def test_logseq_dir_singleton(logseq_dir):
    """Test that the LogseqAnalyzerLogseqDir is a singleton."""
    other_logseq_dir = LogseqDirectory()
    assert logseq_dir is other_logseq_dir
    assert isinstance(logseq_dir, LogseqDirectory)


def test_config_file_singleton(config_file):
    """Test that the ConfigFile is a singleton."""
    other = ConfigFile()
    assert config_file is other
    assert isinstance(config_file, ConfigFile)


def test_delete_directory_singleton(delete_dir):
    """Test that the DeleteDirectory is a singleton."""
    other = DeleteDirectory()
    assert delete_dir is other
    assert isinstance(delete_dir, DeleteDirectory)


def test_delete_bak_directory_singleton(delete_bak_dir):
    """Test that the DeleteBakDirectory is a singleton."""
    other = DeleteBakDirectory()
    assert delete_bak_dir is other
    assert isinstance(delete_bak_dir, DeleteBakDirectory)


def test_delete_recycle_directory_singleton(delete_recycle_dir):
    """Test that the DeleteRecycleDirectory is a singleton."""
    other = DeleteRecycleDirectory()
    assert delete_recycle_dir is other
    assert isinstance(delete_recycle_dir, DeleteRecycleDirectory)


def test_delete_assets_directory_singleton(delete_assets_dir):
    """Test that the DeleteAssetsDirectory is a singleton."""
    other = DeleteAssetsDirectory()
    assert delete_assets_dir is other
    assert isinstance(delete_assets_dir, DeleteAssetsDirectory)


def test_cache_file_singleton(cache_file):
    """Test that the CacheFile is a singleton."""
    other = CacheFile()
    assert cache_file is other
    assert isinstance(cache_file, CacheFile)


def test_bak_directory_singleton(bak_dir):
    """Test that the BakDirectory is a singleton."""
    other = BakDirectory()
    assert bak_dir is other
    assert isinstance(bak_dir, BakDirectory)


def test_recycle_directory_singleton(recycle_dir):
    """Test that the RecycleDirectory is a singleton."""
    other = RecycleDirectory()
    assert recycle_dir is other
    assert isinstance(recycle_dir, RecycleDirectory)


def test_global_config_file_singleton(global_config_file):
    """Test that the GlobalConfigFile is a singleton."""
    other = GlobalConfigFile()
    assert global_config_file is other
    assert isinstance(global_config_file, GlobalConfigFile)


def test_assets_directory_singleton(assets_dir):
    """Test that the AssetsDirectory is a singleton."""
    other = AssetsDirectory()
    assert assets_dir is other
    assert isinstance(assets_dir, AssetsDirectory)


def test_draws_directory_singleton(draws_dir):
    """Test that the DrawsDirectory is a singleton."""
    other = DrawsDirectory()
    assert draws_dir is other
    assert isinstance(draws_dir, DrawsDirectory)


def test_journals_directory_singleton(journals_dir):
    """Test that the JournalsDirectory is a singleton."""
    other = JournalsDirectory()
    assert journals_dir is other
    assert isinstance(journals_dir, JournalsDirectory)


def test_pages_directory_singleton(pages_dir):
    """Test that the PagesDirectory is a singleton."""
    other = PagesDirectory()
    assert pages_dir is other
    assert isinstance(pages_dir, PagesDirectory)


def test_whiteboards_directory_singleton(whiteboards_dir):
    """Test that the WhiteboardsDirectory is a singleton."""
    other = WhiteboardsDirectory()
    assert whiteboards_dir is other
    assert isinstance(whiteboards_dir, WhiteboardsDirectory)
