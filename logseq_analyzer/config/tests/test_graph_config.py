"""
Tests for LogseqGraphConfig.
"""

import pytest

from ..graph_config import LogseqGraphConfig, _get_default_logseq_config_edn


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
    graph_config.user_config_data = {":key1": "value1"}
    graph_config.global_config_data = {":key2": "value2"}
    graph_config.ls_config = graph_config.merge()
    assert (
        graph_config.ls_config[":key1"] == "value1" and graph_config.ls_config[":key2"] == "value2"
    ), "Merged config should contain both user and global data."


def test_default_logseq_config():
    config = _get_default_logseq_config_edn()
    assert config is not None
    assert isinstance(config, dict)
    assert ":meta/version" in config
