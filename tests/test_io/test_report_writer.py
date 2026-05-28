"""Test the ReportWriter class."""

from pathlib import Path

import pytest

from logseq_analyzer.adapter.reporter import ReportWriter


@pytest.fixture
def report_writer() -> ReportWriter:
    """Fixture to create a ReportWriter object."""
    return ReportWriter(Path("test"))


def test_report_writer_init(report_writer: ReportWriter) -> None:
    """Test the initialization of ReportWriter."""
    assert report_writer.root_dirname == Path("test")
