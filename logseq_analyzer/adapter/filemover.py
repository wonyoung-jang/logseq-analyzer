"""File mover for logseq analysis."""

import logging
import shutil
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING

from logseq_analyzer.domain.enums import Output

if TYPE_CHECKING:
    from collections.abc import Iterator, Sized

    from logseq_analyzer.domain.model import LogseqFile

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogseqFileMover:
    """Class to handle moving files and directories in the Logseq Analyzer."""

    should_move_bak: bool
    should_move_recycle: bool
    should_move_unlinked_assets: bool
    unlinked_assets: set[LogseqFile]
    paths: dict[str, Path]
    moved_unlinked_assets: list[str] = field(default_factory=list)
    moved_bak: list[str] = field(default_factory=list)
    moved_recycle: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Set up LogseqFileMover for moving files and directories."""
        self.moved_unlinked_assets = _move(
            self.paths["del_assets"], _yield_asset(self.unlinked_assets), move=self.should_move_unlinked_assets
        )
        self.moved_bak = _move(self.paths["del_bak"], _yield_dir(self.paths["bak"]), move=self.should_move_bak)
        self.moved_recycle = _move(
            self.paths["del_recycle"], _yield_dir(self.paths["recycle"]), move=self.should_move_recycle
        )

    @property
    def report(self) -> tuple[str, list[tuple[str, Sized]]]:
        """Generate a report of the moved files."""
        return (
            Output.Dir.MOVED,
            [
                (
                    Output.File.MOVED,
                    {
                        "assets": self.moved_unlinked_assets,
                        "bak": self.moved_bak,
                        "recycle": self.moved_recycle,
                    },
                )
            ],
        )


def _move(target_dir: Path, paths: Iterator[Path], *, move: bool) -> list[str]:
    """Process the moving of files to a specified directory.

    Args:
        target_dir (Path): The directory to move files to.
        paths (Iterator[Path]): An iterator yielding file paths to move.
        move (bool): If True, move the files. If False, simulate the move.

    Returns:
        list[str]: A list of names of the moved files/folders.

    """
    _paths = list(paths)
    names = [path.name for path in _paths]
    if not names:
        return names
    if not move:
        return ["======== Simulated only ========", *names]
    for src in _paths:
        dest = target_dir / src.name
        try:
            shutil.move(src, dest)
            logger.warning("Moved file: %s to %s", src, dest)
        except shutil.Error, OSError:
            logger.exception("Failed to move file: %s to %s", src, dest)
    return names


def _yield_dir(path: Path) -> Iterator[Path]:
    """Yield the file paths of bak and recycle directories."""
    for root, dirs, files in Path.walk(path):
        for name in chain(dirs, files):
            print(root / name)
            yield root / name


def _yield_asset(unlinked_assets: set[LogseqFile]) -> Iterator[Path]:
    """Yield the file paths of unlinked assets."""
    for asset in unlinked_assets:
        yield asset.path
