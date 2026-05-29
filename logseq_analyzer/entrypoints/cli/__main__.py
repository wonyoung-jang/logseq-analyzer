"""Main entry point for the Logseq Analyzer CLI."""

from logseq_analyzer.app import Args, run_app
from logseq_analyzer.entrypoints.cli.cli import get_cli_args


def main() -> None:
    """Run the Logseq Analyzer application."""
    run_app(args=Args(**get_cli_args()))


if __name__ == "__main__":
    main()
