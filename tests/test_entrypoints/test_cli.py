"""Test the LogseqAnalyzerArguments class."""

import sys

import pytest

from logseq_analyzer.app import Args
from logseq_analyzer.entrypoints.cli.cli import get_cli_args


@pytest.fixture
def args_instance() -> Args:
    """Fixture for LogseqAnalyzerArguments instance."""
    return Args(graph_folder="")


def test_initialization(args_instance: Args) -> None:
    """Test the initial state of the arguments."""
    assert args_instance.graph_folder == ""
    assert args_instance.global_config == ""
    assert args_instance.move_unlinked_assets is False
    assert args_instance.move_bak is False
    assert args_instance.move_recycle is False
    assert args_instance.graph_cache is False
    assert args_instance.report_format == ".txt"


def test_set_gui_args() -> None:
    """Test setting arguments via set_gui_args."""
    gui_args = {
        "graph_folder": "/path/to/graph",
        "global_config": "/path/to/config.ini",
        "move_unlinked_assets": True,
        "move_bak": False,
        "move_recycle": True,
        "graph_cache": True,
        "report_format": ".json",
    }
    args_instance = Args(**gui_args)
    assert args_instance.graph_folder == "/path/to/graph"
    assert args_instance.global_config == "/path/to/config.ini"
    assert args_instance.move_unlinked_assets is True
    assert args_instance.move_bak is False
    assert args_instance.move_recycle is True
    assert args_instance.graph_cache is True
    assert args_instance.report_format == ".json"
    assert not hasattr(args_instance, "non_existent_arg")


def test_set_cli_args_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setting arguments via set_cli_args with basic flags."""
    test_graph_path = "/fake/graph/dir"
    mock_argv = [
        "script_name",
        "--graph-folder",
        test_graph_path,
        "--move-unlinked-assets",
        "--report-format",
        ".md",
    ]
    monkeypatch.setattr(sys, "argv", mock_argv)
    args_instance = Args(**get_cli_args())
    assert args_instance.graph_folder == test_graph_path
    assert args_instance.global_config == ""  # Default argparse value
    assert args_instance.move_unlinked_assets is True
    assert args_instance.move_bak is False  # Default argparse value
    assert args_instance.move_recycle is False  # Default argparse value
    assert args_instance.graph_cache is True  # Default argparse value
    assert args_instance.report_format == ".md"


def test_set_cli_args_all_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setting arguments via set_cli_args with all flags."""
    test_graph_path = "/another/graph"
    test_config_path = "/path/to/global.ini"
    mock_argv = [
        "script_name",
        "--graph-folder",
        test_graph_path,
        "--graph-cache",
        "--move-unlinked-assets",
        "--move-bak",
        "--move-recycle",
        "--global-config",
        test_config_path,
        "--report-format",
        ".json",
    ]
    monkeypatch.setattr(sys, "argv", mock_argv)
    args_instance = Args(**get_cli_args())
    assert args_instance.graph_folder == test_graph_path
    assert args_instance.global_config == test_config_path
    assert args_instance.move_unlinked_assets is True
    assert args_instance.move_bak is True
    assert args_instance.move_recycle is True
    assert args_instance.graph_cache is True
    assert args_instance.report_format == ".json"


def test_set_cli_args_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test default values when using set_cli_args."""
    test_graph_path = "/default/test/graph"
    mock_argv = [
        "script_name",
        "--graph-folder",
        test_graph_path,
        # Only required arg is provided
    ]
    monkeypatch.setattr(sys, "argv", mock_argv)
    args_instance = Args(**get_cli_args())
    assert args_instance.graph_folder == test_graph_path
    assert args_instance.global_config == ""
    assert args_instance.move_unlinked_assets is False
    assert args_instance.move_bak is False
    assert args_instance.move_recycle is False
    assert args_instance.graph_cache is True
    assert args_instance.report_format == ".txt"  # Default value specified in add_argument


def test_set_cli_args_missing_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that argparse raises SystemExit if required arg is missing."""
    mock_argv = [
        "script_name",
        # Missing --graph-folder
        "--write-graph",
    ]
    monkeypatch.setattr(sys, "argv", mock_argv)
    # argparse.parse_args() calls sys.exit() upon error
    with pytest.raises(SystemExit):
        Args(**get_cli_args())
