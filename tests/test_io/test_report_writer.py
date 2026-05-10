"""Test the ReportWriter class."""

from pathlib import Path

import pytest

from logseq_analyzer.io.reporter import ReportWriter


@pytest.fixture
def report_writer() -> ReportWriter:
    """Fixture to create a ReportWriter object."""
    ext = ".md"
    output_dir = "test"
    return ReportWriter(ext, Path(output_dir))


def test_report_writer_init(report_writer: ReportWriter) -> None:
    """Test the initialization of ReportWriter."""
    assert report_writer.ext == ".md"
    assert report_writer.output_dir == Path("test")
