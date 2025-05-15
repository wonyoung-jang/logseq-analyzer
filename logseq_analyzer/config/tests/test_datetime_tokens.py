"""
Test the LogseqDateTimeTokens class.
"""

import pytest
import re

from ..graph_config import LogseqGraphConfig
from ..analyzer_config import LogseqAnalyzerConfig
from ..datetime_tokens import LogseqDateTimeTokens, LogseqJournalFormats


@pytest.fixture
def datetime_tokens():
    """Fixture for LogseqDateTimeTokens."""
    dtt = LogseqDateTimeTokens()
    return dtt


def test_singleton_instance(datetime_tokens):
    """Test that LogseqDateTimeTokens is a singleton."""
    instance1 = LogseqDateTimeTokens()
    instance2 = LogseqDateTimeTokens()
    assert instance1 is instance2
    assert instance1 is datetime_tokens


def test_get_datetime_token_map(datetime_tokens):
    """Test the get_token_map method."""
    datetime_tokens.get_datetime_token_map(LogseqAnalyzerConfig())
    assert datetime_tokens.token_map is not None
    assert isinstance(datetime_tokens.token_map, dict), "Datetime token map should be a dictionary."
    assert len(datetime_tokens.token_map) > 0, "Datetime token map should not be empty."
    assert all(isinstance(k, str) for k in datetime_tokens.token_map.keys()), "Keys should be strings."
    assert all(isinstance(v, str) for v in datetime_tokens.token_map.values()), "Values should be strings."
    assert all(len(k) > 0 for k in datetime_tokens.token_map.keys()), "Keys should not be empty strings."
    assert all(len(v) > 0 for v in datetime_tokens.token_map.values()), "Values should not be empty strings."
    assert all(k != v for k, v in datetime_tokens.token_map.items()), "Keys and values should not be the same."
    assert all(k != "" for k in datetime_tokens.token_map.keys()), "Keys should not be empty strings."
    assert all(v != "" for v in datetime_tokens.token_map.values()), "Values should not be empty strings."


def test_set_datetime_token_pattern(datetime_tokens):
    """Test the set_datetime_token_pattern method."""
    datetime_tokens.get_datetime_token_map(LogseqAnalyzerConfig())
    datetime_tokens.set_datetime_token_pattern()
    assert datetime_tokens.token_pattern is not None, "Datetime token pattern should be set."
    assert isinstance(datetime_tokens.token_pattern, re.Pattern), "Datetime token pattern should be a compiled regex."
    assert len(datetime_tokens.token_pattern.pattern) > 0, "Datetime token pattern should not be empty."
    assert all(isinstance(k, str) for k in datetime_tokens.token_map.keys()), "Keys should be strings."
    assert all(isinstance(v, str) for v in datetime_tokens.token_map.values()), "Values should be strings."
    assert all(len(k) > 0 for k in datetime_tokens.token_map.keys()), "Keys should not be empty strings."
    assert all(len(v) > 0 for v in datetime_tokens.token_map.values()), "Values should not be empty strings."
    assert all(k != v for k, v in datetime_tokens.token_map.items()), "Keys and values should not be the same."


def test_convert_cljs_date_to_py(datetime_tokens):
    """Test the convert_cljs_date_to_py method."""
    datetime_tokens.get_datetime_token_map(LogseqAnalyzerConfig())
    test_format = "yyyy-MM-dd"
    converted_format = datetime_tokens.convert_cljs_date_to_py(test_format)
    assert isinstance(converted_format, str), "Converted format should be a string."
    assert len(converted_format) > 0, "Converted format should not be empty."
    assert all(isinstance(k, str) for k in datetime_tokens.token_map.keys()), "Keys should be strings."
    assert all(isinstance(v, str) for v in datetime_tokens.token_map.values()), "Values should be strings."
    assert all(len(k) > 0 for k in datetime_tokens.token_map.keys()), "Keys should not be empty strings."
    assert all(len(v) > 0 for v in datetime_tokens.token_map.values()), "Values should not be empty strings."
    assert all(k != v for k, v in datetime_tokens.token_map.items()), "Keys and values should not be the same."
    assert all(k != "" for k in datetime_tokens.token_map.keys()), "Keys should not be empty strings."
    assert all(v != "" for v in datetime_tokens.token_map.values()), "Values should not be empty strings."
    assert converted_format != test_format, "Converted format should not be the same as the original format."
    assert converted_format != "", "Converted format should not be an empty string."
    assert converted_format != None, "Converted format should not be None."


def test_replace_token(datetime_tokens):
    """Test the replace_token method."""
    datetime_tokens.get_datetime_token_map(LogseqAnalyzerConfig())
    test_string = "yyyy-MM-dd"
    match = datetime_tokens.token_pattern.search(test_string)
    assert match is not None, "Match should not be None."
    replaced_string = datetime_tokens.replace_token(match)
    assert isinstance(replaced_string, str), "Replaced string should be a string."
    assert len(replaced_string) > 0, "Replaced string should not be empty."
    assert replaced_string != test_string, "Replaced string should not be the same as the original string."
    assert replaced_string != "", "Replaced string should not be an empty string."
    assert replaced_string != None, "Replaced string should not be None."
    assert all(isinstance(k, str) for k in datetime_tokens.token_map.keys()), "Keys should be strings."
