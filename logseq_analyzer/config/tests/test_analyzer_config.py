"""
Test the AnalyzerConfig class in the logseq_analyzer.config module.
"""

from pathlib import Path
import pytest

from ..analyzer_config import LogseqAnalyzerConfig, lambda_optionxform
from ...utils.enums import Constants


@pytest.fixture
def config():
    """Fixture for LogseqAnalyzerConfig."""
    return LogseqAnalyzerConfig(Path(Constants.CONFIG_INI_FILE.value))


def test_singleton(config):
    """Test that LogseqAnalyzerConfig is a singleton."""
    config1 = config
    config2 = LogseqAnalyzerConfig()
    assert config1 is config2, "LogseqAnalyzerConfig should be a singleton."
    assert config1.config is config2.config, "Config objects should be the same instance."


def test_init(config):
    """Test the initialization of LogseqAnalyzerConfig."""
    assert config.config is not None, "Config should be initialized."
    assert config.target_dirs == set(), "Target directories should be empty on initialization."


def test_lambda_optionxform():
    """Test the lambda_optionxform function."""
    assert lambda_optionxform("TEST") == "TEST", "lambda_optionxform should preserve case."
    assert lambda_optionxform("test") == "test", "lambda_optionxform should preserve case."
    assert lambda_optionxform("Test") == "Test", "lambda_optionxform should preserve case."


def test_get_set(config):
    """Test the get and set methods."""
    config.set_value("TEST_SECTION", "test_key", "test_value")
    assert config["TEST_SECTION"]["test_key"] == "test_value", "get should return the correct value."


def test_get_section(config):
    """Test the get_section method."""
    config.set_value("TEST_SECTION", "test_key", "test_value")
    section = config["TEST_SECTION"]
    assert section["test_key"] == "test_value", "get_section should return the correct section."

    non_section = config["NON_EXISTENT_SECTION"]
    assert non_section == {}, "get_section should return an empty dict for non-existent sections."


def test_write(config, tmp_path):
    """Test the write method."""
    config.set_value("TEST_SECTION", "test_key", "test_value")
    test_file = tmp_path / "test_config.ini"
    with open(test_file, "w") as f:
        config.config.write(f)

    # Read back the file to verify
    with open(test_file, "r") as f:
        content = f.read()
    assert "[TEST_SECTION]\n" in content, "Written file should contain the section."
    assert "test_key = test_value\n" in content, "Written file should contain the key-value pair."


def test_write_to_file_overwrites_existing(config, tmp_path):
    """Test that write_to_file overwrites existing files."""
    # Prepare a dummy configuration and a pre-existing file with old content
    config.set_value("SECTION1", "key1", "value1")
    out_file = tmp_path / "user_config.ini"
    out_file.write_text("OLD_CONTENT", encoding="utf-8")
    # Write new config to the same path
    config.write_to_file(str(out_file))
    # Read back and ensure old content was replaced
    content = out_file.read_text(encoding="utf-8")
    assert "OLD_CONTENT" not in content
    assert "[SECTION1]" in content
    assert "key1 = value1" in content


def test_set_logseq_config_edn_data(config):
    """Test the set_logseq_config_edn_data method."""
    ls_config = {
        ":pages-directory": "pages",
        ":journals-directory": "journals",
        ":whiteboards-directory": "whiteboards",
        ":file/name-format": ":triple-lowbar",
    }
    config.set_logseq_config_edn_data(ls_config)
    assert config["LOGSEQ_CONFIG"]["DIR_PAGES"] == "pages", "DIR_PAGES should be set correctly."
    assert config["LOGSEQ_CONFIG"]["DIR_JOURNALS"] == "journals", "DIR_JOURNALS should be set correctly."
    assert config["LOGSEQ_CONFIG"]["DIR_WHITEBOARDS"] == "whiteboards", "DIR_WHITEBOARDS should be set correctly."
    assert config["LOGSEQ_CONFIG"]["NAMESPACE_FORMAT"] == ":triple-lowbar", "NAMESPACE_FORMAT should be set correctly."
    assert config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"] == "___", "NAMESPACE_FILE_SEP should be set correctly."
    ls_config.update(
        {
            ":file/name-format": ":legacy",
        }
    )
    config.set_logseq_config_edn_data(ls_config)
    assert config["LOGSEQ_CONFIG"]["NAMESPACE_FORMAT"] == ":legacy", "NAMESPACE_FORMAT should be set correctly."
    assert config["LOGSEQ_NAMESPACES"]["NAMESPACE_FILE_SEP"] == "%2F", "NAMESPACE_FILE_SEP should be set correctly."


def test_set_logseq_target_dirs(config):
    """Test the set_logseq_target_dirs method."""
    config.set_value("LOGSEQ_CONFIG", "DIR_ASSETS", "assets")
    config.set_value("LOGSEQ_CONFIG", "DIR_DRAWS", "draws")
    config.set_value("LOGSEQ_CONFIG", "DIR_PAGES", "pages")
    config.set_value("LOGSEQ_CONFIG", "DIR_JOURNALS", "journals")
    config.set_value("LOGSEQ_CONFIG", "DIR_WHITEBOARDS", "whiteboards")
    config.set_logseq_target_dirs()
    expected_dirs = {"assets", "draws", "pages", "journals", "whiteboards"}
    assert config.target_dirs == expected_dirs, "Target directories should be set correctly."
