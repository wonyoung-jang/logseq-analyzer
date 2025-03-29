"""
Setup module for Logseq Analyzer.
"""

import argparse

from .compile_regex import RegexPatterns
from .config_loader import Config


CONFIG = Config.get_instance()
PATTERNS = RegexPatterns.get_instance()


def get_logseq_analyzer_args(**kwargs: dict) -> argparse.Namespace:
    """
    Setup the command line arguments for the Logseq Analyzer.

    Args:
        **kwargs: Keyword arguments for GUI mode.

    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    if kwargs:
        args = argparse.Namespace(
            graph_folder=kwargs.get("graph_folder"),
            global_config=kwargs.get("global_config_file"),
            move_unlinked_assets=kwargs.get("move_assets", False),
            move_bak=kwargs.get("move_bak", False),
            move_recycle=kwargs.get("move_recycle", False),
            write_graph=kwargs.get("write_graph", False),
            graph_cache=kwargs.get("graph_cache", False),
            report_format=kwargs.get("report_format", ""),
        )
        return args

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
        help="report format (.txt, .json)",
    )

    return parser.parse_args()
