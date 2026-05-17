"""Argument parsing and CLI entry point for Logseq Analyzer."""

import argparse


def get_cli_args() -> dict:
    """Parse command line arguments and set them as attributes."""
    parser = argparse.ArgumentParser(description="Logseq Analyzer")
    parser.add_argument(
        "--global-config",
        action="store",
        help="path to global configuration file",
        default="",
    )
    parser.add_argument(
        "--graph-cache",
        action="store_true",
        help="reindex graph cache on run",
        default=True,
    )
    parser.add_argument(
        "-g",
        "--graph-folder",
        action="store",
        help="path to your main Logseq graph folder (contains subfolders)",
        required=True,
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
        "--move-unlinked-assets",
        action="store_true",
        help='move unlinked assets to "to-delete/assets" folder',
        default=False,
    )
    parser.add_argument(
        "--report-format",
        action="store",
        help="report format (.txt, .json, .md, .html)",
        default=".txt",
    )
    return vars(parser.parse_args())
