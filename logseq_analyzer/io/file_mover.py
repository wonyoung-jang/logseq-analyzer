"""
Module to handle moving files in a Logseq graph directory.
"""

from pathlib import Path
from typing import List, Tuple
import logging
import shutil

from ..utils.helpers import singleton
from ..analysis.assets import LogseqAssets
from ..config.arguments import LogseqAnalyzerArguments
from ..io.path_validator import LogseqAnalyzerPathValidator


@singleton
class LogseqFileMover:
    """
    Class to handle moving files in a Logseq graph directory.
    """

    def __init__(self):
        """
        Initialize the LogseqFileMover class.
        """
        self.moved_files = {}
        self.delete = LogseqAnalyzerPathValidator().dir_delete.path

    def handle_move_files(self) -> List[str]:
        """
        Handle the moving of unlinked assets, bak, and recycle files to a specified directory.
        """
        if LogseqAssets().not_backlinked:
            if LogseqAnalyzerArguments().move_unlinked_assets:
                self.move_unlinked_assets()
                LogseqAssets().not_backlinked = [asset.path.name for asset in LogseqAssets().not_backlinked]
                return LogseqAssets().not_backlinked
            LogseqAssets().not_backlinked = ["=== Simulated only ==="] + [
                asset.path.name for asset in LogseqAssets().not_backlinked
            ]
            return LogseqAssets().not_backlinked
        return []

    def move_unlinked_assets(self) -> None:
        """
        Move unlinked assets to a separate directory.
        """
        delete_asset_dir = LogseqAnalyzerPathValidator().dir_delete_assets.path
        for asset in LogseqAssets().not_backlinked:
            file_path = asset.file_path
            new_path = delete_asset_dir / file_path.name
            try:
                shutil.move(file_path, new_path)
                logging.warning("Moved unlinked asset: %s to %s", file_path, new_path)
            except (shutil.Error, OSError) as e:
                logging.error("Failed to move unlinked asset: %s to %s: %s", file_path, new_path, e)

    def handle_move_directory(self, argument: bool, output_dir: Path, logseq_dir: Path) -> List[str]:
        """
        Move bak and recycle files to a specified directory.
        """
        moved, moved_names = self.get_all_folder_content(output_dir, logseq_dir)

        if moved:
            if argument:
                LogseqFileMover.move_all_folder_content(moved)
                return moved_names
            moved_names = ["=== Simulated only ==="] + moved_names
            return moved_names
        return []

    def get_all_folder_content(self, output_dir: Path, logseq_dir: Path):
        """
        Move all folders from one directory to another.
        """
        moved_content = []
        moved_content_names = []
        for root, dirs, files in Path.walk(logseq_dir):
            for directory in dirs:
                current_dir_path = Path(root) / directory
                moved_dir_path = output_dir / directory
                moved_content.append((current_dir_path, moved_dir_path))
                moved_content_names.append(directory)
            for file in files:
                current_file_path = Path(root) / file
                moved_file_path = output_dir / file
                moved_content.append((current_file_path, moved_file_path))
                moved_content_names.append(file)
        return moved_content, moved_content_names

    @staticmethod
    def move_all_folder_content(moved_content: List[Tuple]) -> None:
        """
        Move all folders from one directory to another.

        Args:
            moved_content (List[Tuple]): List of tuples containing source and destination paths.
        """
        for old_path, new_path in moved_content:
            try:
                shutil.move(old_path, new_path)
                logging.warning("Moved folder: %s to %s", old_path, new_path)
            except (shutil.Error, OSError) as e:
                logging.error("Failed to move folder: %s to %s: %s", old_path, new_path, e)
