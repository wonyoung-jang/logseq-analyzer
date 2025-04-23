# tests/test_cache.py

import shelve
import time

import pytest

import logseq_analyzer.io.cache as cache_module
from ...utils.enums import Output, OutputDir


class DummyShelf(dict):
    """A very basic dict-like shelf with a close method."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._closed = False

    def close(self):
        self._closed = True


@pytest.fixture(autouse=True)
def reset_singleton_and_shelve(monkeypatch, tmp_path):
    """
    Reset the singleton instance between tests, and
    stub out shelve.open and CacheFile so we never hit the real filesystem.
    """
    # --- Stub shelve.open to return DummyShelf ---
    monkeypatch.setattr(shelve, "open", lambda path, protocol: DummyShelf())

    # --- Stub CacheFile so its .path points into tmp_path ---
    class DummyCacheFile:
        def __init__(self):
            # use tmp_path / "cache.db" as our cache file
            self.path = str(tmp_path / "cache.db")

    monkeypatch.setattr(cache_module, "CacheFile", DummyCacheFile)

    # Ensure no previous instance
    if hasattr(cache_module.Cache, "_instance"):
        del cache_module.Cache._instance

    yield

    # Clean up after
    inst = getattr(cache_module.Cache, "_instance", None)
    if inst:
        inst.close()
        del cache_module.Cache._instance


def test_update_get_and_clear():
    cache = cache_module.Cache()
    # update and get
    cache.update({"foo": "bar"})
    assert cache.get("foo") == "bar"
    # default
    assert cache.get("nope", default=123) == 123

    # clear removes everything
    cache.clear()
    assert cache.get("foo") is None


def test_yield_deleted_files_and_clear_deleted_files(tmp_path, monkeypatch):
    # Prepare two temp files: one that exists, one that does not
    keep = tmp_path / "keep.txt"
    delete = tmp_path / "gone.txt"
    keep.write_text("hello")
    # 'delete' file is never created

    # Create a dummy FileIndex with those two
    removed = []

    class DummyFile:
        def __init__(self, path):
            self.file_path = path

    class DummyIndex:
        def __init__(self):
            self.files = [DummyFile(keep), DummyFile(delete)]

        def remove(self, file_obj):
            removed.append(file_obj)

    # Monkey-patch FileIndex so Cache.clear_deleted_files uses our DummyIndex
    monkeypatch.setattr(cache_module, "FileIndex", lambda: DummyIndex())

    cache = cache_module.Cache()
    # Pre-populate some keys so `clear_deleted_files` will write empty dicts
    cache.cache[OutputDir.META.value] = {}
    for k in (
        OutputDir.JOURNALS.value,
        OutputDir.SUMMARY_FILES.value,
        OutputDir.SUMMARY_CONTENT.value,
        OutputDir.NAMESPACES.value,
        OutputDir.MOVED_FILES.value,
    ):
        cache.cache[k] = {"x": "y"}
    cache.clear_deleted_files()

    # After clearing, only the non-existent file should have been removed
    assert len(removed) == 1
    assert removed[0].file_path == delete


def test_iter_modified_files(tmp_path, monkeypatch):
    # Create two files under a dummy "graph" directory
    graph_dir = tmp_path / "graph"
    graph_dir.mkdir()
    f1 = graph_dir / "one.txt"
    f2 = graph_dir / "two.txt"
    f1.write_text("1")
    f2.write_text("2")

    # Make sure they have distinct mtimes
    time.sleep(0.01)
    f2.write_text("2 again")

    # Monkey-patch GraphDirectory.path to point at our tmp graph_dir
    class DummyGraphDir:
        def __init__(self):
            self.path = graph_dir

    monkeypatch.setattr(cache_module, "GraphDirectory", DummyGraphDir)

    # Monkey-patch LogseqAnalyzerConfig.target_dirs to include graph_dir
    class DummyConfig:
        def __init__(self):
            self.target_dirs = [graph_dir]

    monkeypatch.setattr(cache_module, "LogseqAnalyzerConfig", DummyConfig)

    # Monkey-patch iter_files to simply yield both files
    monkeypatch.setattr(cache_module, "iter_files", lambda base, dirs: [f1, f2])

    cache = cache_module.Cache()

    # First pass: both files should be "modified"
    mods = list(cache.iter_modified_files())
    assert set(mods) == {f1, f2}
    # The mod‐tracker should now have entries for both
    mt = cache.cache[Output.MOD_TRACKER.value]
    assert str(f1) in mt and str(f2) in mt

    # Second pass: no files changed, so nothing new
    mods2 = list(cache.iter_modified_files())
    assert mods2 == []
