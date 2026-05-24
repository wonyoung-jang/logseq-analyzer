"""File system operations for Logseq Analyzer."""

import logging
import shutil
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

logger = logging.getLogger(__name__)


class File:
    """Constants used in the Logseq Analyzer."""

    class App(StrEnum):
        """Application-level constants."""

        CACHE_FILE = "logseq_analyzer_cache.db"
        OUTPUT_DIR = "logseq_analyzer_analysis"
        TO_DELETE_ASSETS_DIR = "assets"
        TO_DELETE_DIR = "logseq_analyzer_to_delete"

    class Logseq(StrEnum):
        """Logseq graph structure components."""

        BAK = "bak"
        CONFIG_EDN = "config.edn"
        LOGSEQ = "logseq"
        RECYCLE = ".recycle"


def get_paths(graph_folder: str, config_global: str | None) -> dict[str, Path]:
    """Set up Logseq analyzer configuration based on arguments."""
    graph = Path(graph_folder)
    logseq = graph / File.Logseq.LOGSEQ
    del_dir = Path(File.App.TO_DELETE_DIR)
    paths = {
        "cache": Path(File.App.CACHE_FILE),
        "output": Path(File.App.OUTPUT_DIR),
        "graph": graph,
        "logseq": logseq,
        "bak": logseq / File.Logseq.BAK,
        "recycle": logseq / File.Logseq.RECYCLE,
        "config_user": logseq / File.Logseq.CONFIG_EDN,
        "del_dir": del_dir,
        "del_bak": del_dir / File.Logseq.BAK,
        "del_recycle": del_dir / File.Logseq.RECYCLE,
        "del_assets": del_dir / File.App.TO_DELETE_ASSETS_DIR,
    }
    if config_global:
        paths["config_global"] = Path(config_global)
        check_path(paths["config_global"], must_exist=True)
    check_path(paths["cache"], create=False)
    check_path(paths["output"], is_dir=True, clean_on_init=True)
    check_path(paths["graph"], is_dir=True, must_exist=True)
    check_path(paths["logseq"], is_dir=True, must_exist=True)
    check_path(paths["bak"], is_dir=True)
    check_path(paths["recycle"], is_dir=True)
    check_path(paths["config_user"], must_exist=True)
    check_path(paths["del_dir"], is_dir=True)
    check_path(paths["del_bak"], is_dir=True)
    check_path(paths["del_recycle"], is_dir=True)
    check_path(paths["del_assets"], is_dir=True)
    return paths


def walk_file(path: Path) -> Iterator[Path]:
    """Yield the file paths of directories."""
    for root, _, files in path.walk():
        yield from (root / f for f in files)


def walk_filter(graph: Path, target: set[str], exclude_suffix: str = ".org") -> Iterator[Path]:
    """Recursively iterate over files in the root directory."""
    for root, dirs, files in graph.walk():
        if root == graph:
            dirs[:] = [d for d in dirs if d in target]
            continue
        logger.debug("Processing directory: %s", root)
        yield from (root / f for f in files if not f.endswith(exclude_suffix))


def read_content(path: Path) -> str:
    """Read the content of a file."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError, ValueError:
        return ""


def determine_move(paths: Iterable[Path], target_dir: Path) -> Iterator[tuple[Path, Path]]:
    """Get the names of files that would be moved to a target directory."""
    yield from ((p, target_dir / p.name) for p in paths)


def move_files(paths: Iterable[tuple[Path, Path]]) -> Iterator[str]:
    """Move files from source to destination paths."""
    for src, dest in paths:
        move_file(src, dest)
        yield src.name


def move_file(src: Path, dest: Path) -> None:
    """Move a file from src to dest."""
    try:
        shutil.move(src, dest)
        logger.info("Moved file: %s to %s", src, dest)
    except shutil.Error, OSError:
        logger.exception("Failed to move file: %s to %s", src, dest)


def check_must_exist(path: Path, *, is_dir: bool = False) -> None:
    """Validate the file path."""
    if not path.exists():
        logger.error("File does not exist: %s", path)
        msg = f"File does not exist: {path}"
        raise FileNotFoundError(msg)
    if is_dir and not path.is_dir():
        logger.error("Path is not a directory: %s", path)
        msg = f"Path is not a directory: {path}"
        raise NotADirectoryError(msg)
    if not is_dir and not path.is_file():
        logger.error("Path is not a file: %s", path)
        msg = f"Path is not a file: {path}"
        raise FileNotFoundError(msg)
    logger.debug("%s exists", path)


def clean(path: Path, *, is_dir: bool = False) -> None:
    """Clean up the file or directory."""
    try:
        if is_dir:
            shutil.rmtree(path)
            logger.debug("Deleted directory: %s", path)
        else:
            path.unlink()
            logger.debug("Deleted file: %s", path)
    except OSError:
        logger.exception("Error deleting path")
        raise


def make_if_missing(path: Path, *, is_dir: bool = False) -> None:
    """Create the file or directory if it does not exist."""
    try:
        if is_dir:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug("Created directory: %s", path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            logger.debug("Created file: %s", path)
    except OSError:
        logger.exception("Error creating path")
        raise


def check_path(
    path: Path,
    *,
    is_dir: bool = False,
    must_exist: bool = False,
    clean_on_init: bool = False,
    create: bool = True,
) -> None:
    """Check and prepare the file or directory path."""
    if must_exist:
        check_must_exist(path, is_dir=is_dir)
    if clean_on_init and path.exists():
        clean(path, is_dir=is_dir)
    if create and not path.exists():
        make_if_missing(path, is_dir=is_dir)
    logger.debug("Checked path: %s", path)
