import pytest

from ..filesystem import OutputDirectory


@pytest.fixture
def output_dir():
    """Fixture to create a LogseqAnalyzerOutputDir for testing."""
    return OutputDirectory()


def test_output_dir_singleton(output_dir):
    """Test that the LogseqAnalyzerOutputDir is a singleton."""
    other_output_dir = OutputDirectory()
    assert output_dir is other_output_dir
    assert isinstance(output_dir, OutputDirectory)
