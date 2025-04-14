"""
Test the AnalyzerConfig class in the logseq_analyzer.config module.
"""

import pytest

from ..analyzer_config import LogseqAnalyzerConfig, lambda_optionxform


@pytest.fixture
def config():
    """Fixture for LogseqAnalyzerConfig."""
    return LogseqAnalyzerConfig()


def test_singleton(config):
    """Test that LogseqAnalyzerConfig is a singleton."""
    config1 = config
    config2 = LogseqAnalyzerConfig()
    assert config1 is config2, "LogseqAnalyzerConfig should be a singleton."
    assert config1.config is config2.config, "Config objects should be the same instance."


def test_lambda_optionxform():
    """Test the lambda_optionxform function."""
    assert lambda_optionxform("TEST") == "TEST", "lambda_optionxform should preserve case."
    assert lambda_optionxform("test") == "test", "lambda_optionxform should preserve case."
    assert lambda_optionxform("Test") == "Test", "lambda_optionxform should preserve case."


def test_get_set(config):
    """Test the get and set methods."""
    config.set("TEST_SECTION", "test_key", "test_value")
    assert config.get("TEST_SECTION", "test_key") == "test_value", "get should return the correct value."
    assert (
        config.get("TEST_SECTION", "non_existent_key", fallback="fallback_value") == "fallback_value"
    ), "get should return the fallback value for non-existent keys."


def test_get_section(config):
    """Test the get_section method."""
    config.set("TEST_SECTION", "test_key", "test_value")
    section = config.get_section("TEST_SECTION")
    assert section["test_key"] == "test_value", "get_section should return the correct section."
