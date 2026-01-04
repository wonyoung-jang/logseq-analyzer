"""Test the ReportWriter class."""

import pytest

from logseq_analyzer.io.report_writer import ReportWriter


@pytest.fixture
def report_writer():
    """Fixture to create a ReportWriter object."""
    prefix = "test_report"
    data = {
        "key1": "value1",
        "key2": {"subkey1": "subvalue1", "subkey2": ["item1", "item2"]},
        "key3": ["list_item1", "list_item2"],
        "key4": {"set_item1", "set_item2"},
    }
    subdir = "test"
    return ReportWriter(prefix, data, subdir)


def test_report_writer_init(report_writer) -> None:
    """Test the initialization of ReportWriter."""
    assert report_writer.prefix == "test_report"
    assert report_writer.data == {
        "key1": "value1",
        "key2": {"subkey1": "subvalue1", "subkey2": ["item1", "item2"]},
        "key3": ["list_item1", "list_item2"],
        "key4": {"set_item1", "set_item2"},
    }
    assert report_writer.subdir == "test"
