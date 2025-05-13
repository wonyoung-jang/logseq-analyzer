"""
Module to handle moving files in a Logseq graph directory.
"""

import logging
import shutil
from pathlib import Path

from ..analysis.assets import LogseqAssets
from ..config.arguments import Args
from ..utils.helpers import singleton
from .filesystem import DeleteAssetsDirectory, DeleteDirectory


@singleton
class LogseqFileMover:
    """
    Class to handle moving files in a Logseq graph directory.
    """

    def __init__(self) -> None:
        """
        Initialize the LogseqFileMover class.
        """
        delete_dir = DeleteDirectory()
        self.delete = delete_dir.path
        self.moved_files = {}

    def __repr__(self) -> str:
        return f'LogseqFileMover(delete="{self.delete}")'

    def __str__(self) -> str:
        return f"LogseqFileMover: {self.delete}"

    def handle_move_assets(self) -> list[str]:
        """
        Handle the moving of unlinked assets, bak, and recycle files to a specified directory.

        Returns:
            list[str]: A list of names of the moved files/folders.
        """
        lsa = LogseqAssets()
        args = Args()
        if lsa.not_backlinked:
            if args.move_unlinked_assets:
                self.move_unlinked_assets()
                return lsa.not_backlinked
            lsa.not_backlinked.insert(0, "=== Simulated only ===")
            return lsa.not_backlinked
        return []

    def move_unlinked_assets(self) -> None:
        """
        Move unlinked assets to a separate directory.
        """
        lsa = LogseqAssets()
        delete_assets = DeleteAssetsDirectory()
        delete_asset_dir = delete_assets.path
        for asset in lsa.not_backlinked:
            file_path = asset.file_path
            new_path = delete_asset_dir / file_path.name
            try:
                shutil.move(file_path, new_path)
                logging.warning("Moved unlinked asset: %s to %s", file_path, new_path)
            except (shutil.Error, OSError) as e:
                logging.error("Failed to move unlinked asset: %s to %s: %s", file_path, new_path, e)

    def handle_move_directory(self, argument: bool, output_dir: Path, logseq_dir: Path) -> list[str]:
        """
        Move bak and recycle files to a specified directory.

        Args:
            argument (bool): If True, move the files. If False, simulate the move.
            output_dir (Path): The directory to move files to.
            logseq_dir (Path): The directory to move files from.

        Returns:
            list[str]: A list of names of the moved files/folders.
        """
        moved, moved_names = self.get_all_folder_content(output_dir, logseq_dir)

        if not moved:
            return []

        if not argument:
            moved_names.insert(0, "=== Simulated only ===")
            return moved_names

        LogseqFileMover.move_all_folder_content(moved)
        return moved_names

    def get_all_folder_content(self, output_dir: Path, logseq_dir: Path) -> tuple[list[tuple], list[str]]:
        """
        Move all folders from one directory to another.

        Args:
            output_dir (Path): The directory to move files to.
            logseq_dir (Path): The directory to move files from.

        Returns:
            tuple[list[tuple], list[str]]: A tuple containing a list of tuples with source and destination paths,
                                            and a list of names of the moved files/folders.
        """
        moved_content = []
        moved_content_names = []
        for root, dirs, files in Path.walk(logseq_dir):
            for directory in dirs:
                current_dir_path = root / directory
                moved_dir_path = output_dir / directory
                moved_content.append((current_dir_path, moved_dir_path))
                moved_content_names.append(directory)
            for file in files:
                current_file_path = root / file
                moved_file_path = output_dir / file
                moved_content.append((current_file_path, moved_file_path))
                moved_content_names.append(file)
        return moved_content, moved_content_names

    @staticmethod
    def move_all_folder_content(moved_content: list[tuple]) -> None:
        """
        Move all folders from one directory to another.

        Args:
            moved_content (list[Tuple]): list of tuples containing source and destination paths.
        """
        for old_path, new_path in moved_content:
            try:
                shutil.move(old_path, new_path)
                logging.warning("Moved folder: %s to %s", old_path, new_path)
            except (shutil.Error, OSError) as e:
                logging.error("Failed to move folder: %s to %s: %s", old_path, new_path, e)
