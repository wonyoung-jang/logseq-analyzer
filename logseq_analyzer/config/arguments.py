"""LogseqAnalyzerArguments Class."""

import argparse
from dataclasses import dataclass
from typing import Any

from ..utils.enums import Output


@dataclass(slots=True)
class Args:
    """A class to represent command line arguments for the Logseq Analyzer."""

    global_config: str = ""
    graph_cache: bool = False
    graph_folder: str = ""
    move_all: bool = False
    move_bak: bool = False
    move_recycle: bool = False
    move_unlinked_assets: bool = False
    report_format: str = ".txt"
    write_graph: bool = False

    def set_gui_args(self, gui_args: dict[str, Any]) -> None:
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
            "--move-unlinked-assets",
            action="store_true",
            help='move unlinked assets to "to-delete/assets" folder',
            default=False,
        )
        parser.add_argument(
            "--move-bak",
            action="store_true",
            help="move bak files to 'to-delete/bak' folder",
            default=False,
        )
        parser.add_argument(
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
            help="report format (.txt, .json, .md, .html)",
            default=".txt",
        )
        args = parser.parse_args()
        for key, value in vars(args).items():
            setattr(self, key, value)

    @property
    def report(self) -> dict[Output, list[tuple[str, Any]]]:
        """Generate a report of the arguments."""
        slots = getattr(self, "__slots__", [])
        report = ((key, getattr(self, key)) for key in slots)
        return {Output.ARGUMENTS: list(report)}
