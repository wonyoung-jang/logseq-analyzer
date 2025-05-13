"""
Test the ReportWriter class.
"""

import pytest
from ..report_writer import ReportWriter


@pytest.fixture
def report_writer():
    """Fixture to create a ReportWriter object."""
    filename_prefix = "test_report"
    data = {
        "key1": "value1",
        "key2": {"subkey1": "subvalue1", "subkey2": ["item1", "item2"]},
        "key3": ["list_item1", "list_item2"],
        "key4": {"set_item1", "set_item2"},
    }
    type_output = "test"
    return ReportWriter(filename_prefix, data, type_output)


def test_report_writer_init(report_writer):
    """Test the initialization of ReportWriter."""
    assert report_writer.filename_prefix == "test_report"
    assert report_writer.items == {
        "key1": "value1",
        "key2": {"subkey1": "subvalue1", "subkey2": ["item1", "item2"]},
        "key3": ["list_item1", "list_item2"],
        "key4": {"set_item1", "set_item2"},
    }
    assert report_writer.output_subdir == "test"


def test_representation(report_writer):
    """Test the string representation of ReportWriter."""
    assert repr(report_writer) == "ReportWriter(filename_prefix=test_report, items=data, output_subdir=test)"
    assert str(report_writer) == "ReportWriter: test_report, Items: data, Output Subdir: test"
