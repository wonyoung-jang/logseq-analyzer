"""Main entry point for the Logseq Analyzer CLI."""

from logseq_analyzer.app import run_app
from logseq_analyzer.entrypoints.cli.cli import get_cli_args


def main() -> None:
    """Run the Logseq Analyzer application."""
    arguments = get_cli_args()
    run_app(arguments=arguments)


if __name__ == "__main__":
    main()
