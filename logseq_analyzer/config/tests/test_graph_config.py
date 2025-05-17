"""
Tests for LogseqGraphConfig.
"""

import pytest

from ..graph_config import LogseqGraphConfig, DEFAULT_LOGSEQ_CONFIG_EDN


@pytest.fixture
def graph_config():
    """Fixture for LogseqGraphConfig."""
    return LogseqGraphConfig()


def test_singleton_instance(graph_config):
    """Test that LogseqGraphConfig is a singleton."""
    another_instance = LogseqGraphConfig()
    assert graph_config is another_instance, "LogseqGraphConfig should be a singleton."


def test_merge(graph_config):
    """Test the merging of user and global config."""
    graph_config.config_user = {":key1": "value1"}
    graph_config.config_global = {":key2": "value2"}
    graph_config.merge()
    assert (
        graph_config.config_merged[":key1"] == "value1" and graph_config.config_merged[":key2"] == "value2"
    ), "Merged config should contain both user and global data."


def test_default_logseq_config():
    config = DEFAULT_LOGSEQ_CONFIG_EDN
    assert config is not None
    assert isinstance(config, dict)
    assert ":meta/version" in config
