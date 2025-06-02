"""
LogseqAnalyzerArguments Class
"""

import argparse
from typing import Any

from ..utils.enums import Output
from ..utils.helpers import singleton


@singleton
class Args:
    """A class to represent command line arguments for the Logseq Analyzer."""

    __slots__ = (
        "__dict__",
        "global_config",
        "graph_cache",
        "graph_folder",
        "move_all",
        "move_bak",
        "move_recycle",
        "move_unlinked_assets",
        "report_format",
        "write_graph",
    )

    def __init__(self, **gui_args) -> None:
        """Initialize the Args class with default values."""
        self.global_config: str = ""
        self.graph_cache: bool = False
        self.graph_folder: str = ""
        self.move_all: bool = False
        self.move_bak: bool = False
        self.move_recycle: bool = False
        self.move_unlinked_assets: bool = False
        self.report_format: str = ".txt"
        self.write_graph: bool = False
        self.setup_args(**gui_args)

    def setup_args(self, **gui_args) -> None:
        """Set up command line arguments and GUI arguments."""
        if gui_args:
            self.set_gui_args(**gui_args)
        else:
            self.set_cli_args()

    def set_gui_args(self, **gui_args) -> None:
        """Set arguments if provided as keyword arguments from GUI."""
        for arg, value in gui_args.items():
            setattr(self, arg, value)

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
            default=False,
        )
        parser.add_argument(
            "--graph-cache",
            action="store_true",
            help="reindex graph cache on run",
            default=True,
        )
        parser.add_argument(
            "--move-all",
            action="store_true",
            help="move all (assets, bak, recycle) to their respective folders in 'to-delete' directory",
            default=False,
        )
        parser.add_argument(
            "-ma",
            "--move-unlinked-assets",
            action="store_true",
            help='move unlinked assets to "to-delete/assets" folder',
            default=False,
        )
        parser.add_argument(
            "-mb",
            "--move-bak",
            action="store_true",
            help="move bak files to 'to-delete/bak' folder",
            default=False,
        )
        parser.add_argument(
            "-mr",
            "--move-recycle",
            action="store_true",
            help="move recycle files to 'to-delete/recycle' folder",
            default=False,
        )
        parser.add_argument(
            "--global-config",
            action="store",
            help="path to global configuration file",
            default="",
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

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the arguments."""
        report = {}
        for key in self.__slots__:
            report[key] = getattr(self, key)
        return {Output.ARGUMENTS.value: report}
