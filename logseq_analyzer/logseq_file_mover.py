"""
Module to handle moving files in a Logseq graph directory.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import logging
import shutil

from .logseq_analyzer import LogseqAnalyzer
from .logseq_analyzer_config import LogseqAnalyzerConfig
from .logseq_graph_config import LogseqGraphConfig
from .logseq_graph import LogseqGraph
from .helpers import get_or_create_file_or_folder


class LogseqFileMover:
    """
    Class to handle moving files in a Logseq graph directory.
    """

    def __init__(
        self,
        analyzer: LogseqAnalyzer,
        analyzer_config: LogseqAnalyzerConfig,
        graph_config: LogseqGraphConfig,
        graph: LogseqGraph,
    ):
        """
        Initialize the LogseqFileMover class.
        """
        self.analyzer = analyzer
        self.analyzer_config = analyzer_config
        self.graph_config = graph_config
        self.graph = graph
        self.graph.handle_assets()
        self.moved_files = {
            "moved_assets": self.handle_move_files(),
            "moved_bak": self.handle_move_directory(
                self.analyzer.args.move_bak,
                self.graph_config.bak_dir,
                self.analyzer_config.config["CONST"]["BAK_DIR"],
            ),
            "moved_recycle": self.handle_move_directory(
                self.analyzer.args.move_recycle,
                self.graph_config.recycle_dir,
                self.analyzer_config.config["CONST"]["RECYCLE_DIR"],
            ),
        }

    def handle_move_files(self) -> List[str]:
        """
        Handle the moving of unlinked assets, bak, and recycle files to a specified directory.
        """
        if self.graph.assets_not_backlinked:
            if self.analyzer.args.move_unlinked_assets:
                self.move_unlinked_assets()
                return self.graph.assets_not_backlinked
            self.graph.assets_not_backlinked = ["=== Simulated only ==="] + self.graph.assets_not_backlinked
            return self.graph.assets_not_backlinked
        return []

    def handle_move_directory(self, argument: bool, target_dir: Path, default_dir: Path) -> List[str]:
        """
        Move bak and recycle files to a specified directory.
        """
        moved, moved_names = self.get_all_folder_content(target_dir, default_dir)

        if moved:
            if argument:
                LogseqFileMover.move_all_folder_content(moved)
                return moved_names
            moved_names = ["=== Simulated only ==="] + moved_names
            return moved_names
        return []

    def move_unlinked_assets(self) -> None:
        """
        Move unlinked assets to a separate directory.
        """
        asset_dir = self.analyzer_config.get("LOGSEQ_CONFIG", "DIR_ASSETS")

        if not asset_dir:
            logging.error("No asset directory found in configuration.")
            return

        to_delete_asset_subdir = get_or_create_file_or_folder(self.analyzer.delete_dir / asset_dir)
        for name in self.graph.assets_not_backlinked:
            file_path = Path(self.graph.data[name]["file_path"])
            new_path = to_delete_asset_subdir / file_path.name
            try:
                shutil.move(file_path, new_path)
                logging.warning("Moved unlinked asset: %s to %s", file_path, new_path)
            except (shutil.Error, OSError) as e:
                logging.error("Failed to move unlinked asset: %s to %s: %s", file_path, new_path, e)

    def get_all_folder_content(self, input_dir: Path, target_subdir: Optional[str] = ""):
        """
        Move all folders from one directory to another.
        """
        for folder in [input_dir, self.analyzer.delete_dir]:
            if not folder.exists():
                return [], []

        if target_subdir:
            self.analyzer.delete_dir = get_or_create_file_or_folder(self.analyzer.delete_dir / target_subdir)

        moved_content = []
        moved_content_names = []

        for root, dirs, files in Path.walk(input_dir):
            for directory in dirs:
                current_dir_path = Path(root) / directory
                moved_dir_path = self.analyzer.delete_dir / directory
                moved_content.append((current_dir_path, moved_dir_path))
                moved_content_names.append(directory)
            for file in files:
                current_file_path = Path(root) / file
                moved_file_path = self.analyzer.delete_dir / file
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
