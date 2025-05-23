"""
LogseqAnalyzerArguments Class
"""

import argparse

from ..utils.helpers import singleton


@singleton
class Args:
    # pylint: disable=R0902
    # Arguments class naturally holds many attributes
    """A class to represent command line arguments for the Logseq Analyzer."""

    __slots__ = (
        "graph_folder",
        "global_config",
        "move_unlinked_assets",
        "move_bak",
        "move_recycle",
        "write_graph",
        "graph_cache",
        "report_format",
        "__dict__",
    )

    def __init__(self) -> None:
        """Initialize the Args class with default values."""
        self.graph_folder: str = ""
        self.global_config: str = ""
        self.move_unlinked_assets: bool = False
        self.move_bak: bool = False
        self.move_recycle: bool = False
        self.write_graph: bool = False
        self.graph_cache: bool = False
        self.report_format: str = ".txt"
        self.__dict__ = {
            "graph_folder": self.graph_folder,
            "global_config": self.global_config,
            "move_unlinked_assets": self.move_unlinked_assets,
            "move_bak": self.move_bak,
            "move_recycle": self.move_recycle,
            "write_graph": self.write_graph,
            "graph_cache": self.graph_cache,
            "report_format": self.report_format,
        }

    def setup_args(self, **kwargs) -> None:
        """Set up command line arguments and GUI arguments."""
        if kwargs:
            self.set_gui_args(**kwargs)
        else:
            self.set_cli_args()

    def set_gui_args(self, **kwargs) -> None:
        """Set arguments if provided as keyword arguments from GUI."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_cli_args(self) -> None:
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
            setattr(self, key, value)
