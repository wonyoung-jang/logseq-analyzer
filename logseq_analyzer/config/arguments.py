"""
Logseq Analyzer Class
"""

from pathlib import Path
import argparse


class LogseqAnalyzerArguments:
    """A class to represent command line arguments for the Logseq Analyzer."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the LogseqAnalyzerArguments class."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self.graph_folder: Path = None
            self.global_config: Path = None
            self.move_unlinked_assets: bool = None
            self.move_bak: bool = None
            self.move_recycle: bool = None
            self.write_graph: bool = None
            self.graph_cache: bool = None
            self.report_format: str = None

    def setup_args(self, **kwargs):
        """Set up command line arguments and GUI arguments."""
        if kwargs:
            self.set_gui_args(**kwargs)
        else:
            self.set_cli_args()

    def set_gui_args(self, **kwargs):
        """Set arguments if provided as keyword arguments from GUI."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_cli_args(self):
        """Parse command line arguments and set them as attributes."""
        parser = argparse.ArgumentParser(description="Logseq Analyzer")
        parser.add_argument(
            "-g",
            "--graph-folder",
            action="store",
            help="path to your main Logseq graph folder (contains subfolders)",
            required=True,
        )
        parser.add_argument(
            "-wg",
            "--write-graph",
            action="store_true",
            help="write all graph content to output folder (warning: may result in large file)",
        )
        parser.add_argument(
            "--graph-cache",
            action="store_true",
            help="reindex graph cache on run",
        )
        parser.add_argument(
            "-ma",
            "--move-unlinked-assets",
            action="store_true",
            help='move unlinked assets to "unlinked_assets" folder',
        )
        parser.add_argument(
            "-mb",
            "--move-bak",
            action="store_true",
            help="move bak files to bak folder in output directory",
        )
        parser.add_argument(
            "-mr",
            "--move-recycle",
            action="store_true",
            help="move recycle files to recycle folder in output directory",
        )
        parser.add_argument(
            "--global-config",
            action="store",
            help="path to global configuration file",
        )
        parser.add_argument(
            "--report-format",
            action="store",
            help="report format (.txt, .json, .md)",
            default=".txt",
        )
        args = parser.parse_args()
        for key, value in vars(args).items():
            if hasattr(self, key):
                setattr(self, key, value)
